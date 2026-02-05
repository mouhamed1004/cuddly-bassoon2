#!/usr/bin/env python
"""
Vérifier si la table PasswordReset existe en base de données
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')

try:
    django.setup()
    from django.db import connection
    from blizzgame.models import PasswordReset
    
    print("🔍 VÉRIFICATION DE LA TABLE PASSWORDRESET")
    print("=" * 50)
    
    # Vérifier si la table existe
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blizzgame_passwordreset';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Table 'blizzgame_passwordreset' existe")
            
            # Vérifier la structure de la table
            cursor.execute("PRAGMA table_info(blizzgame_passwordreset);")
            columns = cursor.fetchall()
            print("\n📋 Structure de la table:")
            for col in columns:
                print(f"   • {col[1]} ({col[2]})")
            
            # Tenter de créer un objet PasswordReset (sans le sauvegarder)
            print("\n🧪 Test de création d'objet PasswordReset...")
            from django.contrib.auth.models import User
            from django.utils import timezone
            
            # Trouver un utilisateur existant
            user = User.objects.first()
            if user:
                test_reset = PasswordReset(
                    user=user,
                    expires_at=timezone.now() + timezone.timedelta(hours=1),
                    ip_address='127.0.0.1'
                )
                print("✅ Objet PasswordReset créé avec succès (non sauvegardé)")
                print(f"   • Token: {test_reset.token}")
                print(f"   • is_valid: {test_reset.is_valid}")
                print(f"   • is_expired: {test_reset.is_expired}")
            else:
                print("⚠️ Aucun utilisateur trouvé pour le test")
            
        else:
            print("❌ Table 'blizzgame_passwordreset' n'existe PAS")
            print("\n📝 Actions à effectuer:")
            print("   1. Appliquer la migration: python manage.py migrate")
            print("   2. Ou créer la migration: python manage.py makemigrations blizzgame")
            
        cursor.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Erreur de configuration Django: {e}")
    import traceback
    traceback.print_exc()
