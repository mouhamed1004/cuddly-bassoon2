#!/usr/bin/env python
"""
Script pour vérifier et corriger la structure de la base de données
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.db import connection

def check_table_structure():
    print("🔍 Vérification de la structure de la base de données...")
    
    with connection.cursor() as cursor:
        # Vérifier la structure de la table UserWarning
        print("\n1. Structure de la table blizzgame_userwarning:")
        cursor.execute("PRAGMA table_info(blizzgame_userwarning)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # Vérifier la structure de la table UserBan
        print("\n2. Structure de la table blizzgame_userban:")
        cursor.execute("PRAGMA table_info(blizzgame_userban)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # Vérifier si les colonnes dispute_id existent
        print("\n3. Vérification des colonnes dispute_id:")
        cursor.execute("PRAGMA table_info(blizzgame_userwarning)")
        warning_columns = [col[1] for col in cursor.fetchall()]
        print(f"   - Colonnes dans UserWarning: {warning_columns}")
        
        cursor.execute("PRAGMA table_info(blizzgame_userban)")
        ban_columns = [col[1] for col in cursor.fetchall()]
        print(f"   - Colonnes dans UserBan: {ban_columns}")
        
        if 'dispute_id' not in warning_columns:
            print("   ❌ Colonne dispute_id manquante dans UserWarning")
            print("   🔧 Ajout de la colonne dispute_id...")
            cursor.execute("ALTER TABLE blizzgame_userwarning ADD COLUMN dispute_id VARCHAR(36) NULL")
            print("   ✅ Colonne dispute_id ajoutée à UserWarning")
        else:
            print("   ✅ Colonne dispute_id présente dans UserWarning")
            
        if 'dispute_id' not in ban_columns:
            print("   ❌ Colonne dispute_id manquante dans UserBan")
            print("   🔧 Ajout de la colonne dispute_id...")
            cursor.execute("ALTER TABLE blizzgame_userban ADD COLUMN dispute_id VARCHAR(36) NULL")
            print("   ✅ Colonne dispute_id ajoutée à UserBan")
        else:
            print("   ✅ Colonne dispute_id présente dans UserBan")
        
        # Vérifier les contraintes de clé étrangère
        print("\n4. Vérification des contraintes de clé étrangère:")
        cursor.execute("PRAGMA foreign_key_list(blizzgame_userwarning)")
        fk_warning = cursor.fetchall()
        print(f"   - Clés étrangères UserWarning: {len(fk_warning)}")
        
        cursor.execute("PRAGMA foreign_key_list(blizzgame_userban)")
        fk_ban = cursor.fetchall()
        print(f"   - Clés étrangères UserBan: {len(fk_ban)}")
        
        # Vérifier les index
        print("\n5. Vérification des index:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='blizzgame_userwarning'")
        warning_indexes = cursor.fetchall()
        print(f"   - Index UserWarning: {[idx[0] for idx in warning_indexes]}")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='blizzgame_userban'")
        ban_indexes = cursor.fetchall()
        print(f"   - Index UserBan: {[idx[0] for idx in ban_indexes]}")

if __name__ == '__main__':
    print("🚀 Correction de la structure de la base de données")
    print("=" * 60)
    
    try:
        check_table_structure()
        print("\n✅ Vérification terminée !")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

