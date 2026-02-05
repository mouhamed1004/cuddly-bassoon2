#!/usr/bin/env python
"""
Script de test pour le nouveau système de feed TikTok-like
"""

import os
import django
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Highlight, HighlightView, Profile
from blizzgame.views import highlights_feed_api, highlights_context_api

def create_test_data():
    """Créer des données de test"""
    print("Création des données de test...")
    
    # Créer des utilisateurs de test
    users = []
    for i in range(5):
        username = f"testuser_{i}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@test.com",
                'first_name': f"Test{i}",
                'last_name': "User"
            }
        )
        users.append(user)
        
        # Créer un profil si nécessaire
        profile, created = Profile.objects.get_or_create(user=user)
    
    # Créer de nombreux highlights de test
    highlights = []
    for i in range(50):  # 50 highlights pour tester la pagination
        user = users[i % len(users)]
        highlight = Highlight.objects.create(
            author=user,
            caption=f"Test highlight #{i+1} - Contenu de test pour vérifier le système",
            hashtags=[f"test{i}", f"highlight{i}", "gaming"],
            expires_at=timezone.now() + timedelta(hours=48)
        )
        highlights.append(highlight)
    
    print(f"Créé {len(highlights)} highlights de test")
    return users, highlights

def test_feed_api():
    """Tester l'API de feed"""
    print("\n=== Test de l'API Feed ===")
    
    factory = RequestFactory()
    
    # Test de chargement initial
    request = factory.get('/api/highlights/feed/?limit=5&offset=0&type=for_you')
    request.user = User.objects.first()
    
    response = highlights_feed_api(request)
    data = json.loads(response.content)
    
    print(f"✓ API Feed - Status: {response.status_code}")
    print(f"✓ Highlights retournés: {len(data.get('highlights', []))}")
    print(f"✓ Has more: {data.get('has_more', False)}")
    
    # Test de pagination
    request = factory.get('/api/highlights/feed/?limit=5&offset=5&type=for_you')
    request.user = User.objects.first()
    
    response = highlights_feed_api(request)
    data = json.loads(response.content)
    
    print(f"✓ Pagination - Highlights page 2: {len(data.get('highlights', []))}")
    
    return data.get('success', False)

def test_context_api():
    """Tester l'API de contexte"""
    print("\n=== Test de l'API Context ===")
    
    factory = RequestFactory()
    
    # Prendre un highlight au milieu
    highlight = Highlight.objects.all()[25]  # Highlight au milieu
    
    request = factory.get(f'/api/highlights/{highlight.id}/context/?type=for_you&before=2&after=3')
    request.user = User.objects.first()
    
    try:
        response = highlights_context_api(request, highlight.id)
        data = json.loads(response.content)
        
        print(f"✓ API Context - Status: {response.status_code}")
        print(f"✓ Highlights avec contexte: {len(data.get('highlights', []))}")
        print(f"✓ Target index: {data.get('target_index', 'N/A')}")
        print(f"✓ Target ID: {data.get('target_id', 'N/A')}")
        
        return data.get('success', False)
    except Exception as e:
        print(f"✗ Erreur API Context: {e}")
        return False

def test_performance():
    """Tester les performances avec de nombreux highlights"""
    print("\n=== Test de Performance ===")
    
    import time
    
    factory = RequestFactory()
    
    # Test de chargement avec différentes tailles de lot
    batch_sizes = [3, 5, 10, 20]
    
    for batch_size in batch_sizes:
        start_time = time.time()
        
        request = factory.get(f'/api/highlights/feed/?limit={batch_size}&offset=0&type=for_you')
        request.user = User.objects.first()
        
        response = highlights_feed_api(request)
        end_time = time.time()
        
        data = json.loads(response.content)
        processing_time = (end_time - start_time) * 1000  # en ms
        
        print(f"✓ Batch size {batch_size}: {processing_time:.2f}ms - {len(data.get('highlights', []))} highlights")

def test_direct_access():
    """Tester l'accès direct via URL"""
    print("\n=== Test d'Accès Direct ===")
    
    highlight = Highlight.objects.all()[10]  # Prendre un highlight spécifique
    
    from blizzgame.views import highlights_for_you
    factory = RequestFactory()
    
    # Test d'accès direct avec paramètre highlight
    request = factory.get(f'/highlights/for-you/?highlight={highlight.id}')
    request.user = User.objects.first()
    
    try:
        response = highlights_for_you(request)
        print(f"✓ Accès direct - Status: {response.status_code}")
        print(f"✓ Mode de chargement: direct")
        return True
    except Exception as e:
        print(f"✗ Erreur accès direct: {e}")
        return False

def cleanup_test_data():
    """Nettoyer les données de test"""
    print("\n=== Nettoyage ===")
    
    # Supprimer les highlights de test
    test_highlights = Highlight.objects.filter(caption__contains="Test highlight")
    count = test_highlights.count()
    test_highlights.delete()
    
    # Supprimer les utilisateurs de test
    test_users = User.objects.filter(username__startswith="testuser_")
    user_count = test_users.count()
    test_users.delete()
    
    print(f"✓ Supprimé {count} highlights de test")
    print(f"✓ Supprimé {user_count} utilisateurs de test")

def main():
    """Fonction principale de test"""
    print("🚀 Test du système TikTok Feed")
    print("="*50)
    
    try:
        # Créer les données de test
        users, highlights = create_test_data()
        
        # Tests
        test_results = []
        test_results.append(test_feed_api())
        test_results.append(test_context_api())
        test_results.append(test_direct_access())
        
        # Test de performance
        test_performance()
        
        # Résultats
        print("\n" + "="*50)
        print("🎯 RÉSULTATS DES TESTS")
        print("="*50)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"✅ Tests réussis: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 TOUS LES TESTS SONT PASSÉS!")
            print("📱 Le système TikTok Feed est prêt à l'utilisation")
        else:
            print("⚠️  Certains tests ont échoué, vérifiez les erreurs ci-dessus")
        
        # Informations sur le système
        print(f"\n📊 Statistiques:")
        print(f"   • Total highlights: {Highlight.objects.count()}")
        print(f"   • Highlights de test: {len(highlights)}")
        print(f"   • Utilisateurs de test: {len(users)}")
        
    except Exception as e:
        print(f"❌ Erreur durant les tests: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyage optionnel
        response = input("\nVoulez-vous nettoyer les données de test? (y/N): ")
        if response.lower() == 'y':
            cleanup_test_data()

if __name__ == '__main__':
    main()
