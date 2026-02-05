#!/usr/bin/env python3
"""
SOLUTION RAPIDE: Marque toutes les migrations comme appliquées
À utiliser quand les tables existent déjà dans PostgreSQL
"""
import os
import django
from django.db import connection

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.core.management import call_command

def check_table_exists(table_name):
    """Vérifie si une table existe dans PostgreSQL"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

def main():
    print("🎭 DÉTECTION ET RÉSOLUTION DES MIGRATIONS")
    print("=" * 45)
    
    try:
        # Vérifier si les tables existent déjà
        if check_table_exists('blizzgame_userwarning'):
            print("⚠️  TABLES DÉTECTÉES - Marquage FAKE des migrations...")
            
            # Marquer toutes les migrations comme appliquées
            print("📦 Marquage des migrations Django core...")
            call_command('migrate', 'contenttypes', '--fake')
            call_command('migrate', 'auth', '--fake')
            call_command('migrate', 'admin', '--fake')
            call_command('migrate', 'sessions', '--fake')
            
            print("🎮 Marquage des migrations blizzgame...")
            call_command('migrate', 'blizzgame', '--fake')
            
            print("✅ TOUTES LES MIGRATIONS MARQUÉES COMME APPLIQUÉES")
        else:
            print("✨ NOUVELLE BASE - Migration normale...")
            call_command('migrate')
            print("✅ MIGRATIONS APPLIQUÉES NORMALEMENT")
        
        print("🚀 RÉSOLUTION TERMINÉE AVEC SUCCÈS !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la résolution: {e}")
        print("🔄 Tentative de migration normale en dernier recours...")
        try:
            call_command('migrate')
            print("✅ Migration normale réussie")
        except Exception as e2:
            print(f"❌ Échec total: {e2}")
            raise

if __name__ == "__main__":
    main()
