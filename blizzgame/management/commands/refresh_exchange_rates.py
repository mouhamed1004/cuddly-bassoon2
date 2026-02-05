from django.core.management.base import BaseCommand
from django.utils import timezone
from blizzgame.currency_service import CurrencyService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Rafraîchit tous les taux de change depuis l\'API externe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la mise à jour même si les taux sont récents',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Début du rafraîchissement des taux de change...')
        )
        
        try:
            updated_count = CurrencyService.refresh_all_rates()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Rafraîchissement terminé. {updated_count} taux mis à jour.'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors du rafraîchissement: {e}')
            )
            logger.error(f'Erreur refresh_exchange_rates: {e}')
