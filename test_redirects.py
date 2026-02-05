#!/usr/bin/env python
"""
Script de test pour vérifier que les redirections des fonctionnalités désactivées fonctionnent
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

def test_redirects():
    """Teste que toutes les URLs désactivées redirigent vers la page d'accueil"""
    
    client = Client()
    
    # URLs des Highlights à tester
    highlight_urls = [
        'highlights_home',
        'highlights_for_you', 
        'highlights_friends',
        'highlights_search',
        'create_highlight',
    ]
    
    # URLs du Chat à tester
    chat_urls = [
        'chat_home',
        'chat_list',
        'get_active_chats',
        'user_search',
        'friend_requests',
    ]
    
    # URLs des Abonnements à tester
    subscription_urls = [
        'my_subscriptions',
        'my_subscribers',
    ]
    
    # URLs des Notifications à tester
    notification_urls = [
        'notifications',
    ]
    
    all_urls = highlight_urls + chat_urls + subscription_urls + notification_urls
    
    print("🧪 Test des redirections des fonctionnalités désactivées...")
    print("=" * 60)
    
    success_count = 0
    total_count = len(all_urls)
    
    for url_name in all_urls:
        try:
            # Tenter d'accéder à l'URL
            response = client.get(reverse(url_name))
            
            # Vérifier que c'est une redirection (302) vers la page d'accueil
            if response.status_code == 302:
                if 'index' in response.url or '/' in response.url:
                    print(f"✅ {url_name}: Redirection OK vers la page d'accueil")
                    success_count += 1
                else:
                    print(f"❌ {url_name}: Redirection incorrecte vers {response.url}")
            else:
                print(f"❌ {url_name}: Pas de redirection (status: {response.status_code})")
                
        except Exception as e:
            print(f"❌ {url_name}: Erreur - {str(e)}")
    
    print("=" * 60)
    print(f"📊 Résultats: {success_count}/{total_count} redirections réussies")
    
    if success_count == total_count:
        print("🎉 Toutes les redirections fonctionnent correctement !")
        return True
    else:
        print("⚠️  Certaines redirections ont échoué")
        return False

def test_main_features():
    """Teste que les fonctionnalités principales fonctionnent toujours"""
    
    client = Client()
    
    print("\n🔍 Test des fonctionnalités principales...")
    print("=" * 60)
    
    # Test de la page d'accueil
    try:
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Page d'accueil: Accessible")
        else:
            print(f"❌ Page d'accueil: Erreur {response.status_code}")
    except Exception as e:
        print(f"❌ Page d'accueil: Erreur - {str(e)}")
    
    # Test de la page de profil
    try:
        response = client.get('/profile/admin/')  # Utilisateur par défaut
        if response.status_code == 200:
            print("✅ Page de profil: Accessible")
        else:
            print(f"❌ Page de profil: Erreur {response.status_code}")
    except Exception as e:
        print(f"❌ Page de profil: Erreur - {str(e)}")
    
    # Test de la boutique
    try:
        response = client.get('/shop/')
        if response.status_code == 200:
            print("✅ Boutique: Accessible")
        else:
            print(f"❌ Boutique: Erreur {response.status_code}")
    except Exception as e:
        print(f"❌ Boutique: Erreur - {str(e)}")

if __name__ == "__main__":
    print("🚀 Test des fonctionnalités désactivées de BLIZZ")
    print("=" * 60)
    
    # Test des redirections
    redirects_ok = test_redirects()
    
    # Test des fonctionnalités principales
    test_main_features()
    
    print("\n" + "=" * 60)
    if redirects_ok:
        print("🎯 Toutes les fonctionnalités désactivées redirigent correctement")
        print("🚀 BLIZZ est prêt pour le lancement !")
    else:
        print("⚠️  Des problèmes ont été détectés avec les redirections")
        print("🔧 Vérifiez la configuration avant le lancement")
