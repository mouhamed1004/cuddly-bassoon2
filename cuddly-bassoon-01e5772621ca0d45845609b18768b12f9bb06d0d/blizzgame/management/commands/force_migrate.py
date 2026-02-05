"""
Commande pour forcer l'application des migrations sur Render
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection

class Command(BaseCommand):
    help = 'Force l\'application de toutes les migrations'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 FORÇAGE DES MIGRATIONS SUR RENDER')
        )
        
        try:
            # Appliquer toutes les migrations
            self.stdout.write('📋 Application de toutes les migrations...')
            call_command('migrate', verbosity=2)
            
            # Vérifier l'état des migrations
            self.stdout.write('\n📊 État des migrations:')
            call_command('showmigrations', 'blizzgame')
            
            # Vérifier la structure de la table notification
            self.stdout.write('\n🔍 Vérification de la table notification...')
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA table_info(blizzgame_notification)")
                columns = cursor.fetchall()
                
                self.stdout.write('📋 Colonnes de la table blizzgame_notification:')
                order_column_exists = False
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    self.stdout.write(f'   - {col_name}: {col_type}')
                    if col_name == 'order_id':
                        order_column_exists = True
                
                if order_column_exists:
                    self.stdout.write(
                        self.style.SUCCESS('   ✅ Colonne \'order_id\' trouvée')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('   ❌ Colonne \'order_id\' MANQUANTE')
                    )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Migrations forcées avec succès !')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors du forçage: {e}')
            )
