"""
Commande Django pour nettoyer les médias des annonces vendues
Usage: python manage.py cleanup_sold_posts_media
"""
from django.core.management.base import BaseCommand
from blizzgame.media_cleanup import cleanup_sold_posts_media


class Command(BaseCommand):
    help = 'Nettoie les médias (images et vidéos) des annonces vendues pour économiser l\'espace de stockage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait supprimé sans effectuer la suppression',
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('Mode dry-run activé - aucune suppression ne sera effectuée')
            )
            # TODO: Implémenter le mode dry-run si nécessaire
            return

        self.stdout.write('Début du nettoyage des médias des annonces vendues...')
        
        result = cleanup_sold_posts_media()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Nettoyage terminé avec succès! '
                    f'{result["cleaned_posts"]} annonces nettoyées.'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'Erreur lors du nettoyage: {result["error"]}'
                )
            )
