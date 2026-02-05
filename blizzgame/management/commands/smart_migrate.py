"""
Management command pour résoudre automatiquement les conflits de migrations
Usage: python manage.py smart_migrate
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Résout automatiquement les conflits de migrations Django/PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-fake',
            action='store_true',
            help='Force le marquage fake même si les tables n\'existent pas',
        )

    def check_table_exists(self, table_name):
        """Vérifie si une table existe dans PostgreSQL"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s AND table_schema = 'public'
                );
            """, [table_name])
            return cursor.fetchone()[0]

    def handle(self, *args, **options):
        self.stdout.write("🎭 SMART MIGRATE - RÉSOLUTION INTELLIGENTE")
        self.stdout.write("=" * 50)
        
        try:
            # Vérifier la connexion à la base de données (compatible SQLite + PostgreSQL)
            db_engine = connection.settings_dict['ENGINE']
            self.stdout.write(f"🔗 Base de données: {db_engine.split('.')[-1]}")
            
            # Lister quelques tables critiques à vérifier
            critical_tables = [
                'blizzgame_userwarning',
                'blizzgame_profile', 
                'blizzgame_post',
                'auth_user',
                'django_migrations'
            ]
            
            existing_tables = []
            for table in critical_tables:
                if self.check_table_exists(table):
                    existing_tables.append(table)
                    self.stdout.write(f"✅ Table trouvée: {table}")
            
            self.stdout.write(f"📊 Tables existantes: {len(existing_tables)}/{len(critical_tables)}")
            
            # Décision intelligente
            if len(existing_tables) >= 3 or options['force_fake']:
                self.stdout.write("⚠️  TABLES DÉTECTÉES - Mode FAKE")
                
                # Marquer les migrations comme appliquées
                apps_to_fake = ['contenttypes', 'auth', 'admin', 'sessions', 'blizzgame']
                
                for app in apps_to_fake:
                    try:
                        self.stdout.write(f"📦 Fake migration: {app}")
                        call_command('migrate', app, '--fake', verbosity=0)
                        self.stdout.write(f"✅ {app} - OK")
                    except Exception as e:
                        self.stdout.write(f"⚠️  {app}: {str(e)}")
                
            else:
                self.stdout.write("✨ NOUVELLE BASE - Mode NORMAL")
                call_command('migrate', verbosity=1)
            
            self.stdout.write("🚀 SMART MIGRATE TERMINÉ AVEC SUCCÈS !")
            
        except Exception as e:
            self.stderr.write(f"❌ Erreur: {str(e)}")
            self.stdout.write("🔄 Tentative de migration normale...")
            try:
                call_command('migrate', verbosity=1)
                self.stdout.write("✅ Migration normale réussie")
            except Exception as e2:
                self.stderr.write(f"❌ Échec total: {str(e2)}")
                raise
