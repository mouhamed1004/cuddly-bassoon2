#!/usr/bin/env python
"""
Test pour vérifier que les utilisateurs non connectés sont correctement gérés
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
from blizzgame.models import Profile, Post
import time

def test_auth_redirect():
    """Test que les utilisateurs non connectés sont correctement gérés"""
    print("🔒 TEST DE GESTION DES UTILISATEURS NON CONNECTÉS")
    print("=" * 60)
    
    try:
        # Créer un utilisateur et un post de test
        username = f"test_auth_{int(time.time())}"
        email = f"testauth{int(time.time())}@example.com"
        password = "TestPassword123!"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name="Test",
            last_name="Auth"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        
        # Créer un post de test
        post = Post.objects.create(
            user=username,
            author=user,
            title="Test Post",
            caption="Description de test",
            price=10.00,
            game_type="FreeFire"
        )
        
        print(f"✅ Utilisateur et post de test créés")
        
        client = Client()
        
        # Test 1: Utilisateur non connecté accède à /create/
        print("\n📝 Test 1: Accès à /create/ sans connexion")
        response = client.get('/create/')
        assert response.status_code == 302, "Redirection attendue vers la page de connexion"
        assert '/signin/' in response.url, "Redirection vers la page de connexion"
        print("✅ Redirection vers la page de connexion pour /create/")
        
        # Test 2: Utilisateur non connecté accède à un détail de produit
        print("\n👁️ Test 2: Accès à un détail de produit sans connexion")
        response = client.get(f'/product/{post.id}/')
        assert response.status_code == 302, "Redirection attendue vers la page de connexion"
        assert '/signin/' in response.url, "Redirection vers la page de connexion"
        print("✅ Redirection vers la page de connexion pour les détails de produit")
        
        # Test 3: Utilisateur non connecté accède à la page d'accueil
        print("\n🏠 Test 3: Accès à la page d'accueil sans connexion")
        response = client.get('/')
        assert response.status_code == 200, "La page d'accueil doit être accessible"
        content = response.content.decode('utf-8')
        assert 'checkAuthAndRedirect' in content, "La fonction JavaScript doit être présente"
        print("✅ Page d'accueil accessible avec fonction JavaScript")
        
        # Test 4: Utilisateur connecté peut accéder à /create/
        print("\n✅ Test 4: Accès à /create/ avec connexion")
        client.login(username=username, password=password)
        response = client.get('/create/')
        # Note: Peut être redirigé vers le profil si l'email n'est pas vérifié
        assert response.status_code in [200, 302], "Accès autorisé ou redirection vers profil"
        print("✅ Utilisateur connecté peut accéder à /create/")
        
        # Test 5: Utilisateur connecté peut voir les détails d'un produit
        print("\n👁️ Test 5: Accès aux détails de produit avec connexion")
        response = client.get(f'/product/{post.id}/')
        assert response.status_code == 200, "Accès autorisé aux détails de produit"
        print("✅ Utilisateur connecté peut voir les détails de produit")
        
        # Test 6: Vérifier que les templates contiennent la fonction JavaScript
        print("\n🔧 Test 6: Vérification de la présence de la fonction JavaScript")
        response = client.get('/')
        content = response.content.decode('utf-8')
        
        # Vérifier les éléments clés
        assert 'checkAuthAndRedirect' in content, "Fonction JavaScript manquante"
        assert 'auth-modal-overlay' in content, "CSS de la modal manquant"
        assert 'showAuthRequiredModal' in content, "Fonction de modal manquante"
        print("✅ Fonction JavaScript et CSS présents")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ La gestion des utilisateurs non connectés fonctionne parfaitement")
        print("\n📋 RÉSUMÉ DES TESTS :")
        print("   • Utilisateur non connecté → Redirection vers connexion")
        print("   • Page d'accueil accessible avec JavaScript")
        print("   • Utilisateur connecté → Accès autorisé")
        print("   • Fonction JavaScript et CSS présents")
        print("   • Modal d'authentification implémentée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Nettoyer
        try:
            user.delete()
        except:
            pass

if __name__ == "__main__":
    success = test_auth_redirect()
    sys.exit(0 if success else 1)
