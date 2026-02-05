from django.core.management.base import BaseCommand
from django.utils import timezone
from blizzgame.models import Highlight
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Supprime les Highlights expirés (après 48h) et leurs données associées'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les Highlights qui seraient supprimés sans les supprimer',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Trouver les highlights expirés
        expired_highlights = Highlight.objects.filter(
            expires_at__lt=now,
            is_active=True
        )
        
        count = expired_highlights.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'Mode dry-run: {count} Highlights seraient supprimés')
            )
            
            for highlight in expired_highlights[:10]:  # Afficher les 10 premiers
                self.stdout.write(f'- {highlight.author.username}: {highlight.caption[:50]}...')
            
            if count > 10:
                self.stdout.write(f'... et {count - 10} autres')
        
        else:
            if count > 0:
                # Marquer comme inactifs au lieu de supprimer complètement
                # pour préserver l'historique et les statistiques
                updated_count = expired_highlights.update(is_active=False)
                
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] {updated_count} Highlights expirés désactivés')
                )
                
                # Optionnel: supprimer complètement après 7 jours d'inactivité
                very_old_highlights = Highlight.objects.filter(
                    expires_at__lt=now - timezone.timedelta(days=7),
                    is_active=False
                )
                
                old_count = very_old_highlights.count()
                if old_count > 0:
                    deleted_count, deleted_details = very_old_highlights.delete()
                    self.stdout.write(
                        self.style.WARNING(f'[DEL] {old_count} Highlights très anciens supprimés définitivement')
                    )
                    
                    # Afficher les détails de suppression
                    for model, model_count in deleted_details.items():
                        if model_count > 0:
                            self.stdout.write(f'  - {model}: {model_count} supprimés')
                
                logger.info(f"Nettoyage automatique: {updated_count} Highlights expirés désactivés, {old_count} supprimés définitivement")
            
            else:
                self.stdout.write(
                    self.style.SUCCESS('Aucun Highlight expiré à traiter')
                )