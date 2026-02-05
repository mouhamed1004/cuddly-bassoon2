#!/usr/bin/env python3
"""
Script de diagnostic spécifique pour Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.conf import settings
import logging

# Configuration du logging pour capturer toutes les erreurs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_render_environment():
    print("🔍 Test de l'environnement Render...")
    
    try:
        # Test 1: Variables d'environnement
        print("1. Vérification des variables d'environnement...")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"   DATABASE: {settings.DATABASES['default']['ENGINE']}")
        print(f"   CACHE: {settings.CACHES['default']['BACKEND']}")
        print(f"   SECRET_KEY: {'✅ Présent' if settings.SECRET_KEY else '❌ Manquant'}")
        
        # Test 2: Connexion base de données
        print("2. Test de la base de données...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"   ✅ Connexion DB: {result}")
        
        # Test 3: Cache Redis
        print("3. Test du cache Redis...")
        try:
            from django.core.cache import cache
            cache.set('test_key', 'test_value', 30)
            value = cache.get('test_key')
            print(f"   ✅ Cache Redis: {value}")
        except Exception as e:
            print(f"   ⚠️ Cache Redis: {e}")
        
        # Test 4: Sessions
        print("4. Test des sessions...")
        try:
            from django.contrib.sessions.models import Session
            session_count = Session.objects.count()
            print(f"   ✅ Sessions: {session_count} sessions actives")
        except Exception as e:
            print(f"   ❌ Sessions: {e}")
        
        # Test 5: Utilisateurs
        print("5. Test des utilisateurs...")
        user_count = User.objects.count()
        print(f"   ✅ Utilisateurs: {user_count} utilisateurs")
        
        # Test 6: Posts
        print("6. Test des posts...")
        from blizzgame.models import Post
        post_count = Post.objects.count()
        print(f"   ✅ Posts: {post_count} posts")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans l'environnement Render: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_index_with_error_handling():
    print("\n🔍 Test de la vue index avec gestion d'erreurs...")
    
    try:
        client = Client()
        
        # Trouver un utilisateur de test
        test_user = User.objects.filter(is_active=True).first()
        if not test_user:
            print("   ❌ Aucun utilisateur actif trouvé")
            return False
        
        print(f"   ✅ Utilisateur de test: {test_user.username}")
        
        # Connecter l'utilisateur
        client.force_login(test_user)
        print("   ✅ Utilisateur connecté")
        
        # Test de la page index avec gestion d'erreurs détaillée
        try:
            response = client.get('/')
            print(f"   ✅ Réponse: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Page index chargée avec succès")
                return True
            else:
                print(f"   ❌ Erreur {response.status_code}")
                print(f"   Contenu: {response.content.decode()[:1000]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception lors de l'accès à la page index: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Erreur dans le test de la vue index: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_components():
    print("\n🔍 Test des composants spécifiques...")
    
    try:
        # Test 1: Modèles avec relations
        print("1. Test des modèles avec relations...")
        from blizzgame.models import Post, Profile, UserReputation
        
        # Test des relations
        posts_with_relations = Post.objects.select_related('author', 'author__profile', 'author__userreputation').prefetch_related('images', 'transactions')[:5]
        print(f"   ✅ Posts avec relations: {len(posts_with_relations)}")
        
        for post in posts_with_relations:
            print(f"     - {post.title}: author={post.author}, profile={getattr(post.author, 'profile', None)}, reputation={getattr(post.author, 'userreputation', None)}")
        
        # Test 2: Annotation avec Case/When
        print("2. Test de l'annotation Case/When...")
        from django.db.models import Q, Case, When, IntegerField
        
        posts_annotated = Post.objects.annotate(
            priority=Case(
                When(
                    Q(is_on_sale=True) & Q(is_sold=False) & Q(is_in_transaction=False),
                    then=1
                ),
                When(
                    Q(is_in_transaction=True),
                    then=2
                ),
                When(
                    Q(is_sold=True),
                    then=3
                ),
                default=4,
                output_field=IntegerField()
            )
        )[:5]
        
        print(f"   ✅ Posts annotés: {len(posts_annotated)}")
        for post in posts_annotated:
            print(f"     - {post.title}: priority={post.priority}")
        
        # Test 3: Pagination
        print("3. Test de la pagination...")
        from django.core.paginator import Paginator
        
        paginator = Paginator(posts_annotated, 12)
        page = paginator.get_page(1)
        print(f"   ✅ Pagination: {len(page)} posts sur la page")
        
        # Test 4: Propriétés des posts
        print("4. Test des propriétés des posts...")
        for post in page[:3]:
            try:
                print(f"     - {post.title}")
                print(f"       game_type: {post.game_type}")
                print(f"       get_game_display_name(): {post.get_game_display_name()}")
                print(f"       time_since_created: {post.time_since_created}")
                print(f"       banner: {getattr(post, 'banner', None)}")
                print(f"       has_banner: {getattr(post, 'has_banner', False)}")
            except Exception as e:
                print(f"       ❌ Erreur sur propriétés: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans les composants spécifiques: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 DIAGNOSTIC RENDER - ERREUR 500")
    print("=" * 50)
    
    # Test de l'environnement Render
    env_ok = test_render_environment()
    
    # Test de la vue index avec gestion d'erreurs
    index_ok = test_index_with_error_handling()
    
    # Test des composants spécifiques
    components_ok = test_specific_components()
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DU DIAGNOSTIC RENDER")
    print("=" * 50)
    print(f"🌍 Environnement: {'✅ OK' if env_ok else '❌ ERREUR'}")
    print(f"🏠 Vue index: {'✅ OK' if index_ok else '❌ ERREUR'}")
    print(f"🧩 Composants: {'✅ OK' if components_ok else '❌ ERREUR'}")
    
    if env_ok and index_ok and components_ok:
        print("🎉 Tous les tests Render sont passés !")
        print("💡 L'erreur 500 pourrait être liée à:")
        print("   - Problème de template sur Render")
        print("   - Problème de fichiers statiques")
        print("   - Problème de permissions")
        print("   - Problème de mémoire/ressources")
    else:
        print("🔧 Erreurs détectées - voir les détails ci-dessus")
