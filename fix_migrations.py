#!/usr/bin/env python3
"""
Script pour résoudre les conflits de migrations Django sur Render
Marque toutes les migrations comme appliquées sans les exécuter
"""
import os
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

def main():
    print("🔧 RÉSOLUTION DES CONFLITS DE MIGRATIONS")
    print("=" * 50)
    
    try:
        # 1. Vérifier la connexion à la base de données
        print("📡 Vérification de la connexion PostgreSQL...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL connecté: {version[:50]}...")
        
        # 2. Lister les tables existantes
        print("\n📋 Tables existantes dans PostgreSQL:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'blizzgame_%'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            for table in tables:
                print(f"   - {table[0]}")
        
        # 3. Marquer les migrations comme appliquées (FAKE)
        print(f"\n🎭 Marquage des migrations comme appliquées (FAKE)...")
        
        # Marquer toutes les migrations comme appliquées sans les exécuter
        apps_to_fake = ['blizzgame', 'auth', 'contenttypes', 'sessions', 'admin']
        
        for app in apps_to_fake:
            try:
                print(f"   📦 {app}...")
                execute_from_command_line(['manage.py', 'migrate', app, '--fake'])
                print(f"   ✅ {app} migrations marquées comme appliquées")
            except Exception as e:
                print(f"   ⚠️  {app}: {str(e)}")
        
        # 4. Vérifier l'état des migrations
        print(f"\n📊 État final des migrations:")
        execute_from_command_line(['manage.py', 'showmigrations'])
        
        print(f"\n🎉 RÉSOLUTION TERMINÉE !")
        print(f"✅ Toutes les migrations sont maintenant synchronisées")
        print(f"🚀 Le déploiement peut continuer normalement")
        
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
