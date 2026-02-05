#!/usr/bin/env python
"""
Script de test pour les nouveaux champs de sécurité dans la page settings
Teste l'affichage de l'email et la gestion des mots de passe.
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
from blizzgame.models import EmailVerification, Profile
from django.test import Client
from django.contrib.auth import authenticate
import time

def create_test_user():
    """Créer un utilisateur de test"""
    username = f"test_security_{int(time.time())}"
    email = f"testsecurity{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name="Test",
            last_name="Security"
        )
        
        # Créer le profil
        Profile.objects.create(user=user, id_user=user.id)
        
        # Créer la vérification email
        verification = EmailVerification.objects.create(user=user)
        
        print(f"✅ Utilisateur créé: {username} ({email})")
        return user, verification, password
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        return None, None, None

def test_settings_page_access():
    """Tester l'accès à la page settings"""
    print("\n🧪 TEST 1: Accès à la page settings")
    
    user, verification, password = create_test_user()
    if not user:
        return False
    
    try:
        client = Client()
        
        # Test 1: Accès sans authentification (doit rediriger)
        response = client.get('/settings/')
        assert response.status_code == 302, "Doit rediriger vers la connexion"
        print("✅ Redirection correcte pour utilisateur non connecté")
        
        # Test 2: Connexion et accès à la page
        login_success = client.login(username=user.username, password=password)
        assert login_success, "La connexion doit réussir"
        print("✅ Connexion réussie")
        
        response = client.get('/settings/')
        assert response.status_code == 200, "La page settings doit être accessible"
        print("✅ Page settings accessible")
        
        # Test 3: Vérifier que l'email est affiché
        content = response.content.decode('utf-8')
        assert user.email in content, "L'email de l'utilisateur doit être affiché"
        print(f"✅ Email affiché: {user.email}")
        
        # Test 4: Vérifier le statut de vérification email
        if verification.is_verified:
            assert "Vérifié" in content, "Le statut vérifié doit être affiché"
            print("✅ Statut email vérifié affiché")
        else:
            assert "Non vérifié" in content, "Le statut non vérifié doit être affiché"
            print("✅ Statut email non vérifié affiché")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def test_password_verification():
    """Tester la vérification du mot de passe actuel"""
    print("\n🧪 TEST 2: Vérification du mot de passe actuel")
    
    user, verification, password = create_test_user()
    if not user:
        return False
    
    try:
        client = Client()
        client.login(username=user.username, password=password)
        
        # Test 1: Vérification avec le bon mot de passe
        response = client.post('/verify-current-password/', 
                             data='{"current_password": "' + password + '"}',
                             content_type='application/json')
        
        assert response.status_code == 200, "La requête doit réussir"
        data = response.json()
        assert data['success'] == True, "La vérification doit réussir avec le bon mot de passe"
        print("✅ Vérification avec bon mot de passe réussie")
        
        # Test 2: Vérification avec un mauvais mot de passe
        response = client.post('/verify-current-password/', 
                             data='{"current_password": "WrongPassword123!"}',
                             content_type='application/json')
        
        assert response.status_code == 200, "La requête doit réussir"
        data = response.json()
        assert data['success'] == False, "La vérification doit échouer avec un mauvais mot de passe"
        print("✅ Vérification avec mauvais mot de passe échouée correctement")
        
        # Test 3: Vérification avec mot de passe vide
        response = client.post('/verify-current-password/', 
                             data='{"current_password": ""}',
                             content_type='application/json')
        
        assert response.status_code == 200, "La requête doit réussir"
        data = response.json()
        assert data['success'] == False, "La vérification doit échouer avec un mot de passe vide"
        print("✅ Vérification avec mot de passe vide échouée correctement")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def test_password_update():
    """Tester la mise à jour du mot de passe"""
    print("\n🧪 TEST 3: Mise à jour du mot de passe")
    
    user, verification, old_password = create_test_user()
    if not user:
        return False
    
    try:
        client = Client()
        client.login(username=user.username, password=old_password)
        
        new_password = "NewPassword123!"
        
        # Test 1: Mise à jour avec les bonnes données
        response = client.post('/update-password/', 
                             data=f'{{"current_password": "{old_password}", "new_password": "{new_password}", "confirm_password": "{new_password}"}}',
                             content_type='application/json')
        
        assert response.status_code == 200, "La requête doit réussir"
        data = response.json()
        assert data['success'] == True, "La mise à jour doit réussir"
        print("✅ Mise à jour du mot de passe réussie")
        
        # Test 2: Vérifier que le nouveau mot de passe fonctionne
        user.refresh_from_db()
        auth_user = authenticate(username=user.username, password=new_password)
        assert auth_user is not None, "Le nouveau mot de passe doit fonctionner"
        print("✅ Nouveau mot de passe fonctionnel")
        
        # Test 3: Vérifier que l'ancien mot de passe ne fonctionne plus
        auth_user_old = authenticate(username=user.username, password=old_password)
        assert auth_user_old is None, "L'ancien mot de passe ne doit plus fonctionner"
        print("✅ Ancien mot de passe désactivé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def test_password_validation():
    """Tester la validation des mots de passe"""
    print("\n🧪 TEST 4: Validation des mots de passe")
    
    user, verification, password = create_test_user()
    if not user:
        return False
    
    try:
        client = Client()
        client.login(username=user.username, password=password)
        
        # Test 1: Mot de passe trop court
        response = client.post('/update-password/', 
                             data='{"current_password": "' + password + '", "new_password": "123", "confirm_password": "123"}',
                             content_type='application/json')
        
        data = response.json()
        assert data['success'] == False, "Le mot de passe trop court doit être rejeté"
        assert "8 caractères" in data['message'], "Le message d'erreur doit mentionner la longueur"
        print("✅ Mot de passe trop court rejeté")
        
        # Test 2: Mots de passe qui ne correspondent pas
        response = client.post('/update-password/', 
                             data='{"current_password": "' + password + '", "new_password": "NewPassword123!", "confirm_password": "DifferentPassword123!"}',
                             content_type='application/json')
        
        data = response.json()
        assert data['success'] == False, "Les mots de passe différents doivent être rejetés"
        assert "correspondent pas" in data['message'], "Le message d'erreur doit mentionner la non-correspondance"
        print("✅ Mots de passe différents rejetés")
        
        # Test 3: Mot de passe actuel incorrect
        response = client.post('/update-password/', 
                             data='{"current_password": "WrongPassword123!", "new_password": "NewPassword123!", "confirm_password": "NewPassword123!"}',
                             content_type='application/json')
        
        data = response.json()
        assert data['success'] == False, "Le mot de passe actuel incorrect doit être rejeté"
        assert "incorrect" in data['message'], "Le message d'erreur doit mentionner l'incorrection"
        print("✅ Mot de passe actuel incorrect rejeté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def test_email_display():
    """Tester l'affichage de l'email"""
    print("\n🧪 TEST 5: Affichage de l'email")
    
    user, verification, password = create_test_user()
    if not user:
        return False
    
    try:
        client = Client()
        client.login(username=user.username, password=password)
        
        response = client.get('/settings/')
        content = response.content.decode('utf-8')
        
        # Test 1: Email affiché
        assert user.email in content, "L'email doit être affiché"
        print(f"✅ Email affiché: {user.email}")
        
        # Test 2: Champ email en lecture seule
        assert 'readonly' in content, "Le champ email doit être en lecture seule"
        print("✅ Champ email en lecture seule")
        
        # Test 3: Message d'information
        assert "ne peut pas être modifié" in content, "Le message d'information doit être présent"
        print("✅ Message d'information présent")
        
        # Test 4: Statut de vérification
        if verification.is_verified:
            assert "Vérifié" in content, "Le statut vérifié doit être affiché"
            print("✅ Statut vérifié affiché")
        else:
            assert "Non vérifié" in content, "Le statut non vérifié doit être affiché"
            print("✅ Statut non vérifié affiché")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def main():
    """Fonction principale"""
    print("🔒 TESTS DES CHAMPS DE SÉCURITÉ - PAGE SETTINGS")
    print("=" * 50)
    
    tests = [
        ("Accès à la page settings", test_settings_page_access),
        ("Vérification du mot de passe", test_password_verification),
        ("Mise à jour du mot de passe", test_password_update),
        ("Validation des mots de passe", test_password_validation),
        ("Affichage de l'email", test_email_display),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n📊 RÉSUMÉ DES TESTS")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont réussis ! Les champs de sécurité fonctionnent parfaitement.")
        print("\n📋 FONCTIONNALITÉS VALIDÉES:")
        print("✅ Affichage de l'email (non modifiable)")
        print("✅ Statut de vérification email")
        print("✅ Vérification du mot de passe actuel")
        print("✅ Mise à jour sécurisée du mot de passe")
        print("✅ Validation des mots de passe")
        print("✅ Interface utilisateur sécurisée")
        return True
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
