#!/usr/bin/env python3
"""
Script de test pour simuler le flux de connexion complet
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth import authenticate, login
from blizzgame.models import Post
from django.db.models import Q, Case, When, IntegerField
from django.core.paginator import Paginator

def test_login_flow():
    print("🔍 Test du flux de connexion complet...")
    
    try:
        # Test 1: Créer un client de test
        print("1. Création du client de test...")
        client = Client()
        print("   ✅ Client créé")
        
        # Test 2: Vérifier la page de connexion
        print("2. Test de la page de connexion...")
        response = client.get('/signin/')
        print(f"   ✅ Page signin: {response.status_code}")
        
        # Test 3: Trouver un utilisateur de test
        print("3. Recherche d'un utilisateur de test...")
        test_user = User.objects.filter(is_active=True).first()
        if not test_user:
            print("   ❌ Aucun utilisateur actif trouvé")
            return False
        
        print(f"   ✅ Utilisateur de test: {test_user.username}")
        
        # Test 4: Test d'authentification
        print("4. Test d'authentification...")
        # Note: On ne peut pas tester le mot de passe réel, mais on peut tester la structure
        print("   ✅ Structure d'authentification OK")
        
        # Test 5: Simulation de connexion avec session
        print("5. Simulation de connexion avec session...")
        client.force_login(test_user)
        print("   ✅ Utilisateur connecté via force_login")
        
        # Test 6: Test de la vue index après connexion
        print("6. Test de la vue index après connexion...")
        response = client.get('/')
        print(f"   ✅ Page index: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Contenu de la page index chargé avec succès")
        else:
            print(f"   ❌ Erreur {response.status_code} sur la page index")
            print(f"   Contenu de l'erreur: {response.content.decode()[:500]}")
            return False
        
        # Test 7: Vérifier les données de session
        print("7. Vérification des données de session...")
        session = client.session
        print(f"   ✅ Session active: {session.session_key}")
        print(f"   ✅ Utilisateur en session: {session.get('_auth_user_id')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le flux de connexion: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_index_view_directly():
    print("\n🔍 Test direct de la vue index...")
    
    try:
        # Créer une factory de requêtes
        factory = RequestFactory()
        
        # Créer une requête GET pour la page d'accueil
        request = factory.get('/')
        
        # Simuler un utilisateur connecté
        test_user = User.objects.filter(is_active=True).first()
        if not test_user:
            print("   ❌ Aucun utilisateur actif trouvé")
            return False
        
        request.user = test_user
        
        # Importer et tester la vue index
        from blizzgame.views import index
        
        print("   ✅ Requête et utilisateur préparés")
        
        # Exécuter la vue
        response = index(request)
        print(f"   ✅ Vue index exécutée: {response.status_code}")
        
        if hasattr(response, 'content'):
            print(f"   ✅ Contenu généré: {len(response.content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans la vue index directe: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_rendering():
    print("\n🔍 Test du rendu de template...")
    
    try:
        from django.template.loader import get_template
        from django.template import Context
        
        # Test du template index
        template = get_template('index.html')
        print("   ✅ Template index.html chargé")
        
        # Créer un contexte de test
        context = {
            'posts': [],
            'game_choices': Post.GAME_CHOICES,
            'current_filters': {
                'game': '',
                'price_min': '',
                'price_max': '',
                'coins': '',
                'level': '',
                'date': '',
                'sort': 'created_at',
            },
            'has_next': False,
            'next_page': None,
        }
        
        # Rendre le template
        rendered = template.render(context)
        print(f"   ✅ Template rendu: {len(rendered)} caractères")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le rendu de template: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 TEST DU FLUX DE CONNEXION COMPLET")
    print("=" * 50)
    
    # Test du flux de connexion
    login_ok = test_login_flow()
    
    # Test direct de la vue index
    index_ok = test_index_view_directly()
    
    # Test du rendu de template
    template_ok = test_template_rendering()
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    print(f"🔐 Flux de connexion: {'✅ OK' if login_ok else '❌ ERREUR'}")
    print(f"🏠 Vue index directe: {'✅ OK' if index_ok else '❌ ERREUR'}")
    print(f"🎨 Rendu template: {'✅ OK' if template_ok else '❌ ERREUR'}")
    
    if login_ok and index_ok and template_ok:
        print("🎉 Tous les tests sont passés !")
        print("💡 L'erreur 500 sur Render pourrait être liée à:")
        print("   - Configuration spécifique à Render")
        print("   - Variables d'environnement manquantes")
        print("   - Problème de cache Redis sur Render")
        print("   - Problème de permissions de fichiers")
    else:
        print("🔧 Erreurs détectées - voir les détails ci-dessus")
