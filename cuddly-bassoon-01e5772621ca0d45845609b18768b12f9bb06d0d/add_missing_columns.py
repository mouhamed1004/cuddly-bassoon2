#!/usr/bin/env python
"""
Script pour ajouter toutes les colonnes manquantes aux tables UserWarning et UserBan
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.db import connection

def add_missing_columns():
    print("🔧 Ajout des colonnes manquantes...")
    
    with connection.cursor() as cursor:
        # Colonnes manquantes pour UserWarning
        warning_columns = [
            ("severity", "VARCHAR(10) DEFAULT 'medium'"),
            ("details", "TEXT DEFAULT ''"),
            ("expires_at", "DATETIME NULL"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ]
        
        print("\n1. Ajout des colonnes manquantes à UserWarning:")
        for col_name, col_type in warning_columns:
            try:
                cursor.execute(f"ALTER TABLE blizzgame_userwarning ADD COLUMN {col_name} {col_type}")
                print(f"   ✅ Colonne {col_name} ajoutée")
            except Exception as e:
                if "duplicate column name" in str(e):
                    print(f"   ⚠️  Colonne {col_name} existe déjà")
                else:
                    print(f"   ❌ Erreur pour {col_name}: {e}")
        
        # Colonnes manquantes pour UserBan
        ban_columns = [
            ("details", "TEXT DEFAULT ''"),
            ("starts_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("ends_at", "DATETIME NULL"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ]
        
        print("\n2. Ajout des colonnes manquantes à UserBan:")
        for col_name, col_type in ban_columns:
            try:
                cursor.execute(f"ALTER TABLE blizzgame_userban ADD COLUMN {col_name} {col_type}")
                print(f"   ✅ Colonne {col_name} ajoutée")
            except Exception as e:
                if "duplicate column name" in str(e):
                    print(f"   ⚠️  Colonne {col_name} existe déjà")
                else:
                    print(f"   ❌ Erreur pour {col_name}: {e}")
        
        # Vérifier la structure finale
        print("\n3. Structure finale des tables:")
        cursor.execute("PRAGMA table_info(blizzgame_userwarning)")
        warning_columns = cursor.fetchall()
        print("   UserWarning:")
        for col in warning_columns:
            print(f"      - {col[1]} ({col[2]})")
        
        cursor.execute("PRAGMA table_info(blizzgame_userban)")
        ban_columns = cursor.fetchall()
        print("   UserBan:")
        for col in ban_columns:
            print(f"      - {col[1]} ({col[2]})")

if __name__ == '__main__':
    print("🚀 Ajout des colonnes manquantes")
    print("=" * 60)
    
    try:
        add_missing_columns()
        print("\n✅ Ajout terminé !")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

