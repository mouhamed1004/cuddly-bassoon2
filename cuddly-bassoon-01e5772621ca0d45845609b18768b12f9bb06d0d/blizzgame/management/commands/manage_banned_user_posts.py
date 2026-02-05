"""
Commande de gestion des annonces des utilisateurs bannis
Cette commande nettoie et gère les annonces selon le statut des utilisateurs
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from blizzgame.post_management import (
    cleanup_banned_user_posts,
    restore_unbanned_user_posts,
    restore_warned_user_posts
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Gère les annonces des utilisateurs bannis et non bannis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['cleanup', 'restore', 'both', 'warnings'],
            default='both',
            help='Action à effectuer: cleanup (désactiver annonces bannis), restore (réactiver annonces non bannis), warnings (gérer avertissements), both (tout)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation - ne fait que rapporter ce qui serait fait'
        )

    def handle(self, *args, **options):
        action = options['action']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 MODE SIMULATION - Aucune modification ne sera effectuée')
            )
        
        total_affected = 0
        
        try:
            if action in ['cleanup', 'both']:
                self.stdout.write('🔍 Nettoyage des annonces des utilisateurs bannis...')
                
                if dry_run:
                    # En mode simulation, on compte seulement
                    from blizzgame.models import UserBan, Post
                    banned_users = UserBan.objects.filter(
                        is_active=True
                    ).exclude(ends_at__lt=timezone.now())
                    
                    total_posts = 0
                    for ban in banned_users:
                        posts = Post.objects.filter(
                            author=ban.user,
                            is_on_sale=True
                        ).exclude(is_sold=True)
                        total_posts += posts.count()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'📊 {banned_users.count()} utilisateurs bannis trouvés')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'📊 {total_posts} annonces seraient désactivées')
                    )
                else:
                    count = cleanup_banned_user_posts()
                    total_affected += count
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {count} annonces désactivées')
                    )
            
            if action in ['restore', 'both']:
                self.stdout.write('🔄 Restauration des annonces des utilisateurs non bannis...')
                
                if dry_run:
                    # En mode simulation, on compte seulement
                    from blizzgame.models import UserBan, Post
                    expired_bans = UserBan.objects.filter(
                        is_active=True,
                        ends_at__lt=timezone.now()
                    )
                    
                    total_posts = 0
                    for ban in expired_bans:
                        posts = Post.objects.filter(
                            author=ban.user,
                            is_sold=False
                        ).exclude(is_in_transaction=True)
                        total_posts += posts.count()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'📊 {expired_bans.count()} bannissements expirés trouvés')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'📊 {total_posts} annonces seraient réactivées')
                    )
                else:
                    count = restore_unbanned_user_posts()
                    total_affected += count
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {count} annonces réactivées')
                    )
            
            if action in ['warnings', 'both']:
                self.stdout.write('⚠️ Gestion des annonces des utilisateurs avec avertissements graves...')
                
                if dry_run:
                    # En mode simulation, on compte seulement
                    from blizzgame.models import UserWarning, Post
                    expired_warnings = UserWarning.objects.filter(
                        is_active=True,
                        severity__in=['high', 'critical'],
                        expires_at__lt=timezone.now()
                    )
                    
                    total_posts = 0
                    for warning in expired_warnings:
                        posts = Post.objects.filter(
                            author=warning.user,
                            is_sold=False
                        ).exclude(is_in_transaction=True)
                        total_posts += posts.count()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'📊 {expired_warnings.count()} avertissements graves expirés trouvés')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'📊 {total_posts} annonces seraient réactivées')
                    )
                else:
                    count = restore_warned_user_posts()
                    total_affected += count
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {count} annonces réactivées suite aux avertissements expirés')
                    )
            
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'🎉 Opération terminée: {total_affected} annonces affectées')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('🎉 Simulation terminée - Aucune modification effectuée')
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la gestion des annonces: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur: {e}')
            )
            raise
