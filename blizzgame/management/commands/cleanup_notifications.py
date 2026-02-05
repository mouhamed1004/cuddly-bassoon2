from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from blizzgame.models import Notification

class Command(BaseCommand):
    help = 'Supprime les anciennes notifications (sauf chat et avertissements)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours après lesquels supprimer les notifications (défaut: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait supprimé sans rien supprimer'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Date limite
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Types de notifications à exclure de la suppression
        excluded_types = [
            'new_message',  # Messages de chat
            'dispute_message',  # Messages de litige
            'warning',  # Avertissements
        ]
        
        # Récupérer les notifications à supprimer
        notifications_to_delete = Notification.objects.filter(
            created_at__lt=cutoff_date
        ).exclude(
            type__in=excluded_types
        )
        
        count = notifications_to_delete.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] {count} notifications seraient supprimées '
                    f'(plus anciennes que {days} jours, excluant: {", ".join(excluded_types)})'
                )
            )
            
            # Afficher quelques exemples
            examples = notifications_to_delete[:5]
            for notif in examples:
                self.stdout.write(f'  - {notif.type}: {notif.title} ({notif.created_at})')
            
            if count > 5:
                self.stdout.write(f'  ... et {count - 5} autres')
        else:
            if count > 0:
                notifications_to_delete.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {count} notifications supprimées avec succès'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Aucune notification à supprimer')
                )
