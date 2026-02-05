#!/usr/bin/env python
"""
Script de débogage pour le système de mot de passe oublié
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
    print("🔧 DÉBOGAGE SYSTÈME MOT DE PASSE OUBLIÉ")
    print("=" * 50)
    
    # Test 1: Configuration email
    print("📧 1. Vérification configuration email")
    from django.conf import settings
    
    required_settings = [
        'EMAIL_BACKEND', 'EMAIL_HOST', 'EMAIL_PORT', 
        'EMAIL_USE_TLS', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD'
    ]
    
    for setting in required_settings:
        value = getattr(settings, setting, 'NON DÉFINI')
        if setting == 'EMAIL_HOST_PASSWORD':
            value = '***' if value else 'NON DÉFINI'
        print(f"   • {setting}: {value}")
    
    # Test 2: Import du modèle
    print("\n🗃️ 2. Vérification du modèle PasswordReset")
    try:
        from blizzgame.models import PasswordReset
        print("   ✅ Import du modèle réussi")
        
        # Vérifier les méthodes
        methods = ['is_valid', 'is_expired', 'mark_as_used', 'send_reset_email']
        for method in methods:
            if hasattr(PasswordReset, method):
                print(f"   ✅ Méthode {method} présente")
            else:
                print(f"   ❌ Méthode {method} manquante")
                
    except Exception as e:
        print(f"   ❌ Erreur import: {e}")
    
    # Test 3: Base de données
    print("\n💾 3. Vérification base de données")
    try:
        from django.db import connection
        cursor = connection.cursor()
        
        # Vérifier si la table existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blizzgame_passwordreset';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("   ✅ Table blizzgame_passwordreset existe")
        else:
            print("   ❌ Table blizzgame_passwordreset n'existe PAS")
            print("   💡 Solution: Appliquer la migration")
            
        cursor.close()
        
    except Exception as e:
        print(f"   ❌ Erreur DB: {e}")
    
    # Test 4: Test d'envoi d'email simple
    print("\n📤 4. Test d'envoi d'email simple")
    try:
        from django.core.mail import send_mail
        
        print("   🔄 Tentative d'envoi d'email de test...")
        result = send_mail(
            subject='Test BLIZZ',
            message='Ceci est un test.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],  # S'envoyer à soi-même
            fail_silently=False
        )
        print(f"   ✅ Email de test envoyé (résultat: {result})")
        
    except Exception as e:
        print(f"   ❌ Erreur envoi email: {type(e).__name__}: {e}")
        if 'Authentication failed' in str(e):
            print("   💡 Problème d'authentification Gmail")
        elif 'Connection refused' in str(e):
            print("   💡 Problème de connexion SMTP")
        
    # Test 5: Utilisateurs existants
    print("\n👥 5. Vérification utilisateurs")
    try:
        from django.contrib.auth.models import User
        user_count = User.objects.count()
        print(f"   • Nombre d'utilisateurs: {user_count}")
        
        if user_count > 0:
            user = User.objects.first()
            print(f"   • Premier utilisateur: {user.username} ({user.email})")
        
    except Exception as e:
        print(f"   ❌ Erreur utilisateurs: {e}")
    
    print("\n✅ Débogage terminé")
    print("\n📋 CHECKLIST POUR RÉSOUDRE:")
    print("1. ✅ Vérifier que la table PasswordReset existe")
    print("2. ✅ Tester l'envoi d'email simple")
    print("3. ✅ Vérifier les paramètres Gmail")
    print("4. ✅ Appliquer les migrations si nécessaire")
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()
