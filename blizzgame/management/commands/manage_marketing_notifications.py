"""
Commande de gestion des notifications marketing
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from blizzgame.models import MarketingNotification, Product
from blizzgame.marketing_utils import MarketingNotificationManager, MarketingProductSelector
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Gère les notifications marketing de la boutique dropshipping'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['cleanup', 'stats', 'test', 'create-for-user'],
            required=True,
            help='Action à effectuer'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Nom d\'utilisateur pour l\'action create-for-user'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours pour le nettoyage (défaut: 30)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'cleanup':
            self.cleanup_notifications(options['days'])
        elif action == 'stats':
            self.show_stats()
        elif action == 'test':
            self.test_system()
        elif action == 'create-for-user':
            if not options['username']:
                raise CommandError('--username est requis pour create-for-user')
            self.create_for_user(options['username'])

    def cleanup_notifications(self, days):
        """Nettoie les anciennes notifications"""
        self.stdout.write(f'Nettoyage des notifications de plus de {days} jours...')
        
        cleaned_count = MarketingNotificationManager.cleanup_old_notifications(days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Nettoyage terminé: {cleaned_count} notifications supprimées')
        )

    def show_stats(self):
        """Affiche les statistiques des notifications"""
        self.stdout.write('=== STATISTIQUES DES NOTIFICATIONS MARKETING ===\n')
        
        # Statistiques générales
        total_notifications = MarketingNotification.objects.count()
        today_notifications = MarketingNotification.objects.filter(
            shown_date=timezone.now().date()
        ).count()
        
        dismissed_today = MarketingNotification.objects.filter(
            shown_date=timezone.now().date(),
            is_dismissed=True
        ).count()
        
        active_today = today_notifications - dismissed_today
        
        self.stdout.write(f'📊 NOTIFICATIONS GÉNÉRALES:')
        self.stdout.write(f'   - Total: {total_notifications}')
        self.stdout.write(f'   - Aujourd\'hui: {today_notifications}')
        self.stdout.write(f'   - Actives aujourd\'hui: {active_today}')
        self.stdout.write(f'   - Fermées aujourd\'hui: {dismissed_today}')
        
        # Produits les plus montrés
        from django.db.models import Count
        popular_products = MarketingNotification.objects.values(
            'product__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        self.stdout.write(f'\n🏆 PRODUITS LES PLUS MONTRÉS:')
        for product in popular_products:
            self.stdout.write(f'   - {product["product__name"]}: {product["count"]} fois')
        
        # Produits éligibles
        eligible_products = MarketingProductSelector.get_eligible_products()
        self.stdout.write(f'\n✅ PRODUITS ÉLIGIBLES: {eligible_products.count()}')
        
        # Dernières notifications
        recent_notifications = MarketingNotification.objects.select_related(
            'user', 'product'
        ).order_by('-created_at')[:5]
        
        self.stdout.write(f'\n📋 DERNIÈRES NOTIFICATIONS:')
        for notification in recent_notifications:
            status = 'Fermée' if notification.is_dismissed else 'Active'
            self.stdout.write(
                f'   - {notification.user.username} | {notification.product.name} | {status}'
            )

    def test_system(self):
        """Teste le système de notifications"""
        self.stdout.write('=== TEST DU SYSTÈME ===\n')
        
        # Test des produits éligibles
        eligible_products = MarketingProductSelector.get_eligible_products()
        self.stdout.write(f'✅ Produits éligibles: {eligible_products.count()}')
        
        if eligible_products.count() == 0:
            self.stdout.write(
                self.style.ERROR('❌ Aucun produit éligible trouvé!')
            )
            return
        
        # Test de sélection de produit
        from django.contrib.auth.models import User
        test_user, created = User.objects.get_or_create(
            username='test_admin_user',
            defaults={'email': 'admin@test.com'}
        )
        
        selected_product = MarketingProductSelector.select_product_for_user(test_user)
        
        if selected_product:
            self.stdout.write(f'✅ Produit sélectionné: {selected_product.name}')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Échec de sélection de produit')
            )
            return
        
        # Test de création de notification
        notification = MarketingNotificationManager.create_daily_notification(test_user)
        
        if notification:
            self.stdout.write(f'✅ Notification créée: {notification.id}')
            
            # Test de fermeture
            success = MarketingNotificationManager.dismiss_notification(
                notification.id, test_user
            )
            
            if success:
                self.stdout.write('✅ Notification fermée avec succès')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Échec de fermeture de notification')
                )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Échec de création de notification')
            )
        
        # Nettoyage
        MarketingNotification.objects.filter(user=test_user).delete()
        if created:
            test_user.delete()
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Test du système réussi!')
        )

    def create_for_user(self, username):
        """Crée une notification pour un utilisateur spécifique"""
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(username=username)
            
            # Nettoyer les anciennes notifications de l'utilisateur
            MarketingNotification.objects.filter(user=user).delete()
            
            # Créer une nouvelle notification
            notification = MarketingNotificationManager.create_daily_notification(user)
            
            if notification:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Notification créée pour {username}: {notification.product.name}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Échec de création pour {username}')
                )
                
        except User.DoesNotExist:
            raise CommandError(f'Utilisateur "{username}" non trouvé')
        except Exception as e:
            raise CommandError(f'Erreur: {e}')
