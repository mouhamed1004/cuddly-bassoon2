#!/usr/bin/env python3
"""
Script de debug pour identifier l'erreur 500 dans la vue index
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, User
from django.db.models import Q, Case, When, IntegerField
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

def test_index_view():
    print("🔍 Test de la vue index...")
    
    try:
        # Test 1: Requête de base
        print("1. Test requête de base...")
        base_posts = Post.objects.select_related('author', 'author__profile', 'author__userreputation').prefetch_related('images', 'transactions')
        print(f"   ✅ {base_posts.count()} posts trouvés")
        
        # Test 2: Filtres
        print("2. Test des filtres...")
        filters = Q()
        print("   ✅ Filtres initialisés")
        
        # Test 3: Annotation avec priority
        print("3. Test annotation priority...")
        posts_query = base_posts.annotate(
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
        )
        print("   ✅ Annotation priority OK")
        
        # Test 4: Tri
        print("4. Test du tri...")
        posts_query = posts_query.order_by('priority', '-created_at')
        print("   ✅ Tri OK")
        
        # Test 5: Pagination
        print("5. Test pagination...")
        paginator = Paginator(posts_query, 12)
        page_number = 1
        posts = paginator.get_page(page_number)
        print(f"   ✅ Pagination OK: {len(posts)} posts sur la page")
        
        # Test 6: Préparation des données pour le template
        print("6. Test préparation données template...")
        game_choices = Post.GAME_CHOICES
        current_filters = {
            'game': '',
            'price_min': '',
            'price_max': '',
            'coins': '',
            'level': '',
            'date': '',
            'sort': 'created_at',
        }
        print("   ✅ Données template préparées")
        
        # Test 7: Test des propriétés des posts
        print("7. Test des propriétés des posts...")
        for i, post in enumerate(posts[:3]):  # Test sur les 3 premiers posts
            try:
                print(f"   Post {i+1}: {post.title}")
                print(f"     - game_type: {post.game_type}")
                print(f"     - get_game_display_name(): {post.get_game_display_name()}")
                print(f"     - price: {post.price}")
                print(f"     - user: {post.user}")
                print(f"     - created_at: {post.created_at}")
                print(f"     - time_since_created: {post.time_since_created}")
                print(f"     - banner: {getattr(post, 'banner', None)}")
                print(f"     - has_banner: {getattr(post, 'has_banner', False)}")
            except Exception as e:
                print(f"   ❌ Erreur sur post {i+1}: {e}")
                import traceback
                traceback.print_exc()
        
        print("✅ Tous les tests de la vue index sont passés !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans la vue index: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_authentication():
    print("\n🔍 Test de l'authentification utilisateur...")
    
    try:
        # Test des utilisateurs
        users = User.objects.all()
        print(f"   ✅ {users.count()} utilisateurs trouvés")
        
        for user in users[:3]:
            print(f"   - {user.username}: {user.email}")
            print(f"     - is_authenticated: {user.is_authenticated}")
            print(f"     - is_active: {user.is_active}")
            print(f"     - has_profile: {hasattr(user, 'profile')}")
            if hasattr(user, 'profile'):
                print(f"     - profile: {user.profile}")
            print(f"     - has_userreputation: {hasattr(user, 'userreputation')}")
            if hasattr(user, 'userreputation'):
                print(f"     - reputation: {user.userreputation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans l'authentification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 DEBUG DE L'ERREUR 500 - VUE INDEX")
    print("=" * 50)
    
    # Test de l'authentification
    auth_ok = test_user_authentication()
    
    # Test de la vue index
    index_ok = test_index_view()
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DU DEBUG")
    print("=" * 50)
    print(f"🔐 Authentification: {'✅ OK' if auth_ok else '❌ ERREUR'}")
    print(f"🏠 Vue Index: {'✅ OK' if index_ok else '❌ ERREUR'}")
    
    if auth_ok and index_ok:
        print("🎉 Aucune erreur détectée dans le code !")
        print("💡 L'erreur 500 pourrait être liée à:")
        print("   - Problème de session Django")
        print("   - Problème de cache/Redis")
        print("   - Problème de template")
        print("   - Problème de permissions")
    else:
        print("🔧 Erreurs détectées - voir les détails ci-dessus")
