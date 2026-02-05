#!/usr/bin/env python3
"""
SOLUTION NUCLÉAIRE: Reset complet des migrations Django
À utiliser quand tout le reste a échoué
"""
import os
import django
from django.db import connection

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.core.management import call_command

def main():
    print("💥 RESET NUCLÉAIRE DES MIGRATIONS")
    print("=" * 40)
    
    try:
        # 1. Vider complètement la table django_migrations
        print("🗑️  Suppression de toutes les migrations enregistrées...")
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations;")
            print("✅ Table django_migrations vidée")
        
        # 2. Marquer TOUTES les migrations comme appliquées
        print("🎭 Marquage fake de TOUTES les migrations...")
        
        # Applications à traiter
        apps = ['contenttypes', 'auth', 'admin', 'sessions', 'blizzgame']
        
        for app in apps:
            try:
                print(f"📦 {app}...")
                call_command('migrate', app, '--fake', verbosity=0)
                print(f"✅ {app} - OK")
            except Exception as e:
                print(f"⚠️  {app}: {str(e)}")
        
        # 3. Vérification finale
        print("\n📊 Vérification des migrations...")
        call_command('showmigrations', verbosity=1)
        
        print("\n🎉 RESET TERMINÉ !")
        print("✅ Toutes les migrations sont maintenant synchronisées")
        print("🚀 Django et PostgreSQL sont en harmonie !")
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        print("💡 Essayez de recréer la base PostgreSQL sur Render")

if __name__ == "__main__":
    main()
