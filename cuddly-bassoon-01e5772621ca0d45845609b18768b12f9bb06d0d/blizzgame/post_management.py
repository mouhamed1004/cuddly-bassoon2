"""
Gestion des annonces basée sur les bannissements et les résultats de litiges
Ce module gère prudemment les changements de statut des annonces
"""

import logging
from django.utils import timezone
from django.db import transaction
from .models import Post, UserBan, Dispute, Transaction

logger = logging.getLogger(__name__)


def is_user_banned(user):
    """
    Vérifie si un utilisateur est actuellement banni
    """
    try:
        active_bans = UserBan.objects.filter(
            user=user,
            is_active=True
        ).exclude(ends_at__lt=timezone.now())
        
        return active_bans.exists()
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du bannissement pour {user.username}: {e}")
        return False


def get_user_active_posts(user):
    """
    Récupère toutes les annonces actives d'un utilisateur
    """
    try:
        return Post.objects.filter(
            author=user,
            is_on_sale=True
        ).exclude(is_sold=True)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des annonces de {user.username}: {e}")
        return Post.objects.none()


def deactivate_user_posts(user, reason="Utilisateur banni"):
    """
    Désactive toutes les annonces d'un utilisateur banni
    """
    try:
        with transaction.atomic():
            posts = get_user_active_posts(user)
            count = 0
            
            for post in posts:
                # Marquer comme non disponible à la vente
                post.is_on_sale = False
                post.is_in_transaction = False
                post.save()
                count += 1
                
                logger.info(f"Annonce {post.id} désactivée pour {user.username}: {reason}")
            
            logger.info(f"{count} annonces désactivées pour {user.username}")
            return count
            
    except Exception as e:
        logger.error(f"Erreur lors de la désactivation des annonces de {user.username}: {e}")
        return 0


def reactivate_user_posts(user, reason="Bannissement levé"):
    """
    Réactive les annonces d'un utilisateur (quand le bannissement est levé)
    """
    try:
        with transaction.atomic():
            posts = Post.objects.filter(
                author=user,
                is_sold=False
            )
            count = 0
            
            for post in posts:
                # Réactiver seulement si pas en transaction
                if not post.is_in_transaction:
                    post.is_on_sale = True
                    post.save()
                    count += 1
                    
                    logger.info(f"Annonce {post.id} réactivée pour {user.username}: {reason}")
            
            logger.info(f"{count} annonces réactivées pour {user.username}")
            return count
            
    except Exception as e:
        logger.error(f"Erreur lors de la réactivation des annonces de {user.username}: {e}")
        return 0


def handle_dispute_resolution_post_status(dispute):
    """
    Gère le statut des annonces après résolution d'un litige
    """
    try:
        if not dispute.resolution:
            logger.warning(f"Litige {dispute.id} sans résolution")
            return False
            
        transaction_obj = dispute.transaction
        post = transaction_obj.post
        
        if dispute.resolution == 'refund':
            # L'acheteur a gagné, le vendeur a perdu
            # L'annonce doit être supprimée
            if post.is_in_transaction:
                post.is_in_transaction = False
                post.is_on_sale = False
                post.is_sold = False
                post.delete()  # Supprimer complètement l'annonce
                logger.info(f"Annonce {post.id} supprimée après remboursement (litige en faveur de l'acheteur)")
                return True
                
        elif dispute.resolution == 'payout':
            # Le vendeur a gagné, l'acheteur a perdu
            # L'annonce reste vendue
            if not post.is_sold:
                post.is_sold = True
                post.is_in_transaction = False
                post.is_on_sale = False
                post.save()
                logger.info(f"Annonce {post.id} marquée comme vendue après paiement vendeur")
                
                # Supprimer les médias de l'annonce vendue pour économiser l'espace
                from .media_cleanup import delete_post_media
                cleanup_result = delete_post_media(post)
                if cleanup_result['success']:
                    logger.info(f"Médias supprimés pour l'annonce {post.id}: {cleanup_result['count']} fichiers")
                else:
                    logger.error(f"Erreur lors de la suppression des médias pour l'annonce {post.id}: {cleanup_result['error']}")
                
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Erreur lors de la gestion du statut de l'annonce pour le litige {dispute.id}: {e}")
        return False


def cleanup_banned_user_posts():
    """
    Nettoie les annonces des utilisateurs bannis (commande de maintenance)
    """
    try:
        banned_users = UserBan.objects.filter(
            is_active=True
        ).exclude(ends_at__lt=timezone.now())
        
        total_deactivated = 0
        
        for ban in banned_users:
            count = deactivate_user_posts(ban.user, f"Bannissement actif: {ban.reason}")
            total_deactivated += count
            
        logger.info(f"Nettoyage terminé: {total_deactivated} annonces désactivées")
        return total_deactivated
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des annonces des utilisateurs bannis: {e}")
        return 0


def restore_unbanned_user_posts():
    """
    Restaure les annonces des utilisateurs non bannis (commande de maintenance)
    """
    try:
        # Utilisateurs avec bannissements expirés
        expired_bans = UserBan.objects.filter(
            is_active=True,
            ends_at__lt=timezone.now()
        )
        
        total_restored = 0
        
        for ban in expired_bans:
            # Désactiver le bannissement
            ban.is_active = False
            ban.save()
            
            # Réactiver les annonces
            count = reactivate_user_posts(ban.user, "Bannissement expiré")
            total_restored += count
            
        logger.info(f"Restauration terminée: {total_restored} annonces réactivées")
        return total_restored
        
    except Exception as e:
        logger.error(f"Erreur lors de la restauration des annonces: {e}")
        return 0


def restore_warned_user_posts():
    """
    Restaure les annonces des utilisateurs dont les avertissements graves ont expiré
    """
    try:
        from .models import UserWarning
        
        # Avertissements graves expirés
        expired_warnings = UserWarning.objects.filter(
            is_active=True,
            severity__in=['high', 'critical'],
            expires_at__lt=timezone.now()
        )
        
        total_restored = 0
        
        for warning in expired_warnings:
            # Désactiver l'avertissement
            warning.is_active = False
            warning.save()
            
            # Réactiver les annonces
            count = reactivate_user_posts(warning.user, "Avertissement expiré")
            total_restored += count
            
        logger.info(f"Restauration des annonces suite aux avertissements expirés: {total_restored} annonces réactivées")
        return total_restored
        
    except Exception as e:
        logger.error(f"Erreur lors de la restauration des annonces suite aux avertissements: {e}")
        return 0
