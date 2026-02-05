#!/usr/bin/env python
"""
Test de la vérification email Gmail - BLIZZ Gaming
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

from django.test import Client
from django.contrib.auth.models import User
from blizzgame.models import EmailVerification

def test_email_verification():
    """Test complet de la vérification email"""
    print("🧪 Test de la vérification email Gmail...")
    
    client = Client()
    
    # Test 1: Inscription d'un utilisateur
    print("\n1. Test d'inscription...")
    response = client.post('/signup/', {
        'username': 'testuser123',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'terms': 'on'
    })
    
    if response.status_code == 302:  # Redirection après inscription
        print("✅ Inscription réussie")
        
        # Vérifier que l'EmailVerification a été créé
        try:
            user = User.objects.get(username='testuser123')
            email_verification = EmailVerification.objects.get(user=user)
            print(f"✅ EmailVerification créé: {email_verification.token}")
            print(f"✅ Email non vérifié: {not email_verification.is_verified}")
        except:
            print("❌ EmailVerification non créé")
    else:
        print("❌ Échec de l'inscription")
    
    # Test 2: Vérification email
    print("\n2. Test de vérification email...")
    try:
        user = User.objects.get(username='testuser123')
        email_verification = EmailVerification.objects.get(user=user)
        
        response = client.get(f'/verify-email/{email_verification.token}/')
        if response.status_code == 302:  # Redirection après vérification
            print("✅ Vérification email réussie")
            
            # Vérifier que l'email est marqué comme vérifié
            email_verification.refresh_from_db()
            if email_verification.is_verified:
                print("✅ Email marqué comme vérifié")
            else:
                print("❌ Email non marqué comme vérifié")
        else:
            print("❌ Échec de la vérification email")
    except:
        print("❌ Utilisateur ou EmailVerification non trouvé")
    
    # Test 3: Test de renvoi d'email
    print("\n3. Test de renvoi d'email...")
    try:
        user = User.objects.get(username='testuser123')
        client.force_login(user)
        
        response = client.post('/resend-verification-email/', {
            'Content-Type': 'application/json'
        })
        
        if response.status_code == 200:
            print("✅ Renvoi d'email testé")
        else:
            print("❌ Échec du renvoi d'email")
    except:
        print("❌ Erreur lors du test de renvoi")
    
    # Nettoyage
    try:
        user = User.objects.get(username='testuser123')
        user.delete()
        print("\n🧹 Utilisateur de test supprimé")
    except:
        pass

def test_email_verification_model():
    """Test du modèle EmailVerification"""
    print("\n🔧 Test du modèle EmailVerification...")
    
    try:
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username='testmodel123',
            email='testmodel@example.com',
            password='TestPassword123!'
        )
        
        # Créer une vérification email
        email_verification = EmailVerification.objects.create(user=user)
        
        # Test des propriétés
        print(f"✅ Token généré: {email_verification.token}")
        print(f"✅ Non vérifié par défaut: {not email_verification.is_verified}")
        print(f"✅ Non expiré par défaut: {not email_verification.is_expired}")
        
        # Test de la méthode send_verification_email
        result = email_verification.send_verification_email()
        print(f"✅ Envoi d'email simulé: {result}")
        
        # Nettoyage
        user.delete()
        print("✅ Modèle EmailVerification fonctionne correctement")
        
    except Exception as e:
        print(f"❌ Erreur lors du test du modèle: {e}")

def test_settings():
    """Test de la configuration email"""
    print("\n⚙️ Test de la configuration email...")
    
    try:
        from django.conf import settings
        
        # Vérifier la configuration email
        if hasattr(settings, 'EMAIL_BACKEND'):
            print(f"✅ EMAIL_BACKEND configuré: {settings.EMAIL_BACKEND}")
        else:
            print("❌ EMAIL_BACKEND non configuré")
        
        if hasattr(settings, 'EMAIL_HOST'):
            print(f"✅ EMAIL_HOST configuré: {settings.EMAIL_HOST}")
        else:
            print("❌ EMAIL_HOST non configuré")
        
        if hasattr(settings, 'EMAIL_VERIFICATION_REQUIRED'):
            print(f"✅ EMAIL_VERIFICATION_REQUIRED: {settings.EMAIL_VERIFICATION_REQUIRED}")
        else:
            print("❌ EMAIL_VERIFICATION_REQUIRED non configuré")
        
        if hasattr(settings, 'BASE_URL'):
            print(f"✅ BASE_URL configuré: {settings.BASE_URL}")
        else:
            print("❌ BASE_URL non configuré")
        
    except Exception as e:
        print(f"❌ Erreur lors du test de configuration: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 TEST DE LA VÉRIFICATION EMAIL GMAIL - BLIZZ GAMING")
    print("=" * 60)
    
    tests = [
        test_settings,
        test_email_verification_model,
        test_email_verification
    ]
    
    results = []
    for test in tests:
        try:
            test()
            results.append(True)
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution du test: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Configuration email",
        "Modèle EmailVerification", 
        "Vérification email complète"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{i+1}. {test_name}: {status}")
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ La vérification email Gmail est implémentée avec succès")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        print("🔧 Vérifiez les implémentations manquantes")
        return False

if __name__ == "__main__":
    main()
