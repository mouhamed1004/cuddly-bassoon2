"""
Utilitaires pour le système de notifications marketing de la boutique dropshipping
"""
import random
import logging
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Q, F, Case, When, IntegerField
from .models import Product, MarketingNotification, User

logger = logging.getLogger(__name__)


class MarketingProductSelector:
    """
    Classe pour sélectionner des produits pour les notifications marketing avec rotation simple
    """
    
    @staticmethod
    def get_eligible_products():
        """
        Récupère les produits éligibles pour les notifications marketing
        """
        return Product.objects.filter(
            status='active',
            shopify_product_id__isnull=False
        ).exclude(
            # Exclure les produits sans image
            featured_image__isnull=True
        ).exclude(
            featured_image=''
        ).order_by('id')  # Ordre fixe pour la rotation
    
    @staticmethod
    def get_user_last_shown_product(user):
        """
        Récupère le dernier produit montré à l'utilisateur
        """
        last_notification = MarketingNotification.objects.filter(
            user=user
        ).order_by('-created_at').first()
        
        if last_notification:
            return last_notification.product
        return None
    
    @staticmethod
    def select_product_for_user(user):
        """
        Sélectionne le prochain produit dans la rotation pour un utilisateur
        """
        try:
            # Récupérer les produits éligibles
            eligible_products = MarketingProductSelector.get_eligible_products()
            
            if not eligible_products.exists():
                logger.warning("Aucun produit éligible pour les notifications marketing")
                return None
            
            # Récupérer le dernier produit montré à l'utilisateur
            last_product = MarketingProductSelector.get_user_last_shown_product(user)
            
            if last_product:
                # Trouver l'index du dernier produit dans la liste
                try:
                    last_index = list(eligible_products).index(last_product)
                    # Prendre le produit suivant (ou le premier si c'était le dernier)
                    next_index = (last_index + 1) % len(eligible_products)
                    selected_product = eligible_products[next_index]
                except ValueError:
                    # Le dernier produit n'est plus dans la liste (supprimé, etc.)
                    selected_product = eligible_products.first()
            else:
                # Premier produit pour cet utilisateur
                selected_product = eligible_products.first()
            
            logger.info(f"Produit sélectionné pour {user.username}: {selected_product.name} (rotation)")
            return selected_product
            
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du produit pour {user.username}: {e}")
            return None


class MarketingNotificationManager:
    """
    Gestionnaire pour les notifications marketing quotidiennes
    """
    
    @staticmethod
    def should_show_notification(user):
        """
        Détermine si une notification marketing doit être affichée à l'utilisateur
        """
        today = timezone.now().date()
        
        # Vérifier si l'utilisateur a déjà reçu une notification aujourd'hui
        existing_notification = MarketingNotification.objects.filter(
            user=user,
            shown_date=today
        ).first()
        
        if existing_notification:
            return False, existing_notification
        
        # Vérifier si l'utilisateur a fermé la notification aujourd'hui
        dismissed_notification = MarketingNotification.objects.filter(
            user=user,
            shown_date=today,
            is_dismissed=True
        ).first()
        
        if dismissed_notification:
            return False, None
        
        return True, None
    
    @staticmethod
    def create_daily_notification(user):
        """
        Crée une notification marketing quotidienne pour un utilisateur
        """
        try:
            # Vérifier si une notification doit être affichée
            should_show, existing = MarketingNotificationManager.should_show_notification(user)
            
            if not should_show:
                return existing
            
            # Sélectionner un produit
            product = MarketingProductSelector.select_product_for_user(user)
            
            if not product:
                logger.warning(f"Aucun produit disponible pour la notification de {user.username}")
                return None
            
            # Créer la notification
            notification = MarketingNotification.objects.create(
                user=user,
                product=product,
                shown_date=timezone.now().date()
            )
            
            logger.info(f"Notification marketing créée pour {user.username}: {product.name}")
            return notification
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification pour {user.username}: {e}")
            return None
    
    @staticmethod
    def get_user_notification(user):
        """
        Récupère la notification marketing active pour un utilisateur
        """
        today = timezone.now().date()
        
        return MarketingNotification.objects.filter(
            user=user,
            shown_date=today,
            is_dismissed=False
        ).first()
    
    @staticmethod
    def dismiss_notification(notification_id, user):
        """
        Ferme une notification marketing
        """
        try:
            notification = MarketingNotification.objects.get(
                id=notification_id,
                user=user
            )
            notification.dismiss()
            logger.info(f"Notification marketing fermée par {user.username}")
            return True
        except MarketingNotification.DoesNotExist:
            logger.warning(f"Notification {notification_id} non trouvée pour {user.username}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la notification: {e}")
            return False
    
    @staticmethod
    def cleanup_old_notifications(days=30):
        """
        Nettoie les anciennes notifications marketing
        """
        try:
            cutoff_date = timezone.now().date() - timedelta(days=days)
            deleted_count = MarketingNotification.objects.filter(
                shown_date__lt=cutoff_date
            ).delete()[0]
            
            logger.info(f"Nettoyage des notifications marketing: {deleted_count} notifications supprimées")
            return deleted_count
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des notifications: {e}")
            return 0
