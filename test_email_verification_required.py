#!/usr/bin/env python
"""
Test pour vérifier que seuls les utilisateurs avec email vérifié peuvent créer des annonces
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Profile, EmailVerification
from django.test import Client
import time

def test_email_verification_required():
    """Test que seuls les utilisateurs avec email vérifié peuvent créer des annonces"""
    print("🔒 TEST DE VÉRIFICATION EMAIL REQUISE POUR CRÉER DES ANNONCES")
    print("=" * 60)
    
    # Créer deux utilisateurs de test
    username_verified = f"test_verified_{int(time.time())}"
    username_unverified = f"test_unverified_{int(time.time())}"
    email_verified = f"testverified{int(time.time())}@example.com"
    email_unverified = f"testunverified{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    try:
        # Utilisateur avec email vérifié
        user_verified = User.objects.create_user(
            username=username_verified,
            email=email_verified,
            password=password,
            first_name="Test",
            last_name="Verified"
        )
        
        Profile.objects.create(user=user_verified, id_user=user_verified.id)
        email_verification_verified = EmailVerification.objects.create(
            user=user_verified,
            is_verified=True
        )
        print(f"✅ Utilisateur avec email vérifié créé: {username_verified}")
        
        # Utilisateur avec email non vérifié
        user_unverified = User.objects.create_user(
            username=username_unverified,
            email=email_unverified,
            password=password,
            first_name="Test",
            last_name="Unverified"
        )
        
        Profile.objects.create(user=user_unverified, id_user=user_unverified.id)
        email_verification_unverified = EmailVerification.objects.create(
            user=user_unverified,
            is_verified=False
        )
        print(f"✅ Utilisateur avec email non vérifié créé: {username_unverified}")
        
        client = Client()
        
        # Test 1: Utilisateur avec email vérifié peut accéder à /create/
        print("\n📝 Test 1: Accès à /create/ avec email vérifié")
        client.login(username=username_verified, password=password)
        response = client.get('/create/')
        assert response.status_code == 200, "L'utilisateur avec email vérifié doit pouvoir accéder à /create/"
        print("✅ Utilisateur avec email vérifié peut accéder à /create/")
        
        # Test 2: Utilisateur avec email non vérifié ne peut pas accéder à /create/
        print("\n🚫 Test 2: Accès à /create/ avec email non vérifié")
        client.login(username=username_unverified, password=password)
        response = client.get('/create/')
        assert response.status_code == 302, "L'utilisateur avec email non vérifié doit être redirigé"
        assert f'/profile/{username_unverified}/' in response.url, "Redirection vers le profil attendue"
        print("✅ Utilisateur avec email non vérifié est redirigé vers son profil")
        
        # Test 3: Vérifier le message d'erreur
        print("\n💬 Test 3: Vérification du message d'erreur")
        # Le message d'erreur sera dans la session, on peut le vérifier en accédant au profil
        response = client.get(f'/profile/{username_unverified}/')
        content = response.content.decode('utf-8')
        assert 'vérifier votre email' in content.lower(), "Le message d'erreur doit être affiché"
        print("✅ Message d'erreur affiché correctement")
        
        # Test 4: Utilisateur sans EmailVerification ne peut pas accéder
        print("\n❌ Test 4: Utilisateur sans EmailVerification")
        user_no_verification = User.objects.create_user(
            username=f"test_no_verification_{int(time.time())}",
            email=f"testnoverification{int(time.time())}@example.com",
            password=password
        )
        Profile.objects.create(user=user_no_verification, id_user=user_no_verification.id)
        
        client.login(username=user_no_verification.username, password=password)
        response = client.get('/create/')
        assert response.status_code == 302, "L'utilisateur sans EmailVerification doit être redirigé"
        print("✅ Utilisateur sans EmailVerification est redirigé")
        
        # Test 5: Création d'annonce avec email vérifié
        print("\n📋 Test 5: Création d'annonce avec email vérifié")
        client.login(username=username_verified, password=password)
        response = client.post('/create/', {
            'title': 'Test Annonce',
            'caption': 'Description de test',
            'price': '10.00',
            'game': 'FreeFire',
            'coins': '1000',
            'level': '50'
        })
        assert response.status_code == 302, "La création d'annonce doit réussir"
        print("✅ Annonce créée avec succès par utilisateur vérifié")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ La restriction d'email vérifié fonctionne parfaitement")
        print("\n📋 RÉSUMÉ DES TESTS :")
        print("   • Utilisateur avec email vérifié → Accès autorisé à /create/")
        print("   • Utilisateur avec email non vérifié → Redirection vers profil")
        print("   • Message d'erreur affiché correctement")
        print("   • Utilisateur sans EmailVerification → Redirection")
        print("   • Création d'annonce réussie avec email vérifié")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Nettoyer
        try:
            user_verified.delete()
            user_unverified.delete()
            user_no_verification.delete()
        except:
            pass

if __name__ == "__main__":
    success = test_email_verification_required()
    sys.exit(0 if success else 1)
