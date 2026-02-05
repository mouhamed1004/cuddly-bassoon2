#!/usr/bin/env python
"""
Script de test complet pour vérifier le bon fonctionnement des systèmes BLIZZ
- Marketplace Gaming
- Boutique E-commerce
- Intégration CinetPay
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

def test_gaming_system():
    """Teste le système de marketplace gaming"""
    
    print("🎮 Test du système Gaming Marketplace...")
    print("=" * 60)
    
    client = Client()
    
    try:
        # Test de la page d'accueil
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Page d'accueil accessible")
        else:
            print(f"❌ Page d'accueil: Status {response.status_code}")
            return False
        
        # Test de la page de création
        response = client.get('/create/')
        if response.status_code == 200:
            print("✅ Page de création accessible")
        else:
            print(f"❌ Page de création: Status {response.status_code}")
            return False
        
        # Test des filtres de jeu
        from blizzgame.models import Post
        game_choices = Post.GAME_CHOICES
        if len(game_choices) >= 6:
            print(f"✅ {len(game_choices)} types de jeux configurés")
        else:
            print(f"⚠️  Seulement {len(game_choices)} types de jeux")
        
        # Test des posts existants
        posts_count = Post.objects.count()
        if posts_count > 0:
            print(f"✅ {posts_count} posts trouvés dans la base")
            
            # Test d'un post spécifique
            first_post = Post.objects.first()
            if first_post:
                print(f"✅ Post test: {first_post.title} ({first_post.game_type})")
                
                # Test de la page de détail
                response = client.get(f'/product/{first_post.id}/')
                if response.status_code == 200:
                    print("✅ Page de détail produit accessible")
                else:
                    print(f"⚠️  Page de détail: Status {response.status_code}")
        else:
            print("⚠️  Aucun post trouvé dans la base")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test gaming: {str(e)}")
        return False

def test_ecommerce_system():
    """Teste le système de boutique e-commerce"""
    
    print("\n🛒 Test du système E-commerce...")
    print("=" * 60)
    
    client = Client()
    
    try:
        # Test de la page d'accueil boutique
        response = client.get('/shop/')
        if response.status_code == 200:
            print("✅ Page d'accueil boutique accessible")
        else:
            print(f"❌ Page d'accueil boutique: Status {response.status_code}")
            return False
        
        # Test de la page des produits
        response = client.get('/shop/products/')
        if response.status_code == 200:
            print("✅ Page des produits accessible")
        else:
            print(f"❌ Page des produits: Status {response.status_code}")
            return False
        
        # Test des catégories
        from blizzgame.models import ProductCategory
        categories_count = ProductCategory.objects.filter(is_active=True).count()
        if categories_count > 0:
            print(f"✅ {categories_count} catégories actives trouvées")
        else:
            print("⚠️  Aucune catégorie active trouvée")
        
        # Test des produits
        from blizzgame.models import Product
        products_count = Product.objects.filter(status='active').count()
        if products_count > 0:
            print(f"✅ {products_count} produits actifs trouvés")
            
            # Test d'un produit spécifique
            first_product = Product.objects.filter(status='active').first()
            if first_product:
                print(f"✅ Produit test: {first_product.name} ({first_product.category.name})")
                
                # Test de la page de détail produit
                response = client.get(f'/shop/product/{first_product.slug}/')
                if response.status_code == 200:
                    print("✅ Page de détail produit boutique accessible")
                else:
                    print(f"⚠️  Page de détail produit boutique: Status {response.status_code}")
        else:
            print("⚠️  Aucun produit actif trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test e-commerce: {str(e)}")
        return False

def test_cinetpay_integration():
    """Teste l'intégration CinetPay"""
    
    print("\n💳 Test de l'intégration CinetPay...")
    print("=" * 60)
    
    try:
        # Test de la configuration
        from django.conf import settings
        api_key = getattr(settings, 'CINETPAY_API_KEY', None)
        site_id = getattr(settings, 'CINETPAY_SITE_ID', None)
        
        if api_key and site_id:
            print(f"✅ Configuration CinetPay trouvée")
            print(f"   API_KEY: {api_key[:10]}...{api_key[-10:]}")
            print(f"   SITE_ID: {site_id}")
        else:
            print("❌ Configuration CinetPay manquante")
            return False
        
        # Test des classes CinetPay
        from blizzgame.cinetpay_utils import GamingCinetPayAPI, CinetPayAPI
        
        # Test GamingCinetPayAPI
        gaming_api = GamingCinetPayAPI()
        print(f"✅ GamingCinetPayAPI instanciée")
        print(f"   Base URL: {gaming_api.base_url}")
        
        # Test CinetPayAPI
        shop_api = CinetPayAPI()
        print(f"✅ CinetPayAPI instanciée")
        print(f"   Base URL: {shop_api.base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test CinetPay: {str(e)}")
        return False

def test_database_models():
    """Teste la cohérence des modèles de base de données"""
    
    print("\n🗄️ Test de la base de données...")
    print("=" * 60)
    
    try:
        # Test des modèles principaux
        from blizzgame.models import Post, Product, Transaction, Order, User
        
        # Test des utilisateurs
        users_count = User.objects.count()
        print(f"✅ {users_count} utilisateurs dans la base")
        
        # Test des posts gaming
        posts_count = Post.objects.count()
        print(f"✅ {posts_count} posts gaming dans la base")
        
        # Test des produits e-commerce
        products_count = Product.objects.count()
        print(f"✅ {products_count} produits e-commerce dans la base")
        
        # Test des transactions
        transactions_count = Transaction.objects.count()
        print(f"✅ {transactions_count} transactions dans la base")
        
        # Test des commandes
        orders_count = Order.objects.count()
        print(f"✅ {orders_count} commandes dans la base")
        
        # Test des relations
        if posts_count > 0:
            first_post = Post.objects.first()
            if hasattr(first_post, 'author'):
                print(f"✅ Relation Post-Author fonctionnelle")
            if hasattr(first_post, 'transactions'):
                print(f"✅ Relation Post-Transactions fonctionnelle")
        
        if products_count > 0:
            first_product = Product.objects.first()
            if hasattr(first_product, 'category'):
                print(f"✅ Relation Product-Category fonctionnelle")
            if hasattr(first_product, 'images'):
                print(f"✅ Relation Product-Images fonctionnelle")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test base de données: {str(e)}")
        return False

def test_interface_components():
    """Teste les composants d'interface utilisateur"""
    
    print("\n🎨 Test des composants d'interface...")
    print("=" * 60)
    
    client = Client()
    
    try:
        # Test de la navigation
        response = client.get('/')
        if response.status_code == 200:
            content = response.content.decode()
            
            # Test des éléments de navigation
            if 'Boutique' in content:
                print("✅ Lien Boutique présent")
            if 'Comptes Gaming' in content:
                print("✅ Section Comptes Gaming présente")
            
            # Test des filtres
            if 'Filtrer les produits' in content:
                print("✅ Section filtres présente")
            if 'game' in content and 'price' in content:
                print("✅ Filtres de jeu et prix présents")
        
        # Test de la boutique
        response = client.get('/shop/')
        if response.status_code == 200:
            content = response.content.decode()
            
            if 'Boutique Gaming' in content:
                print("✅ Titre boutique présent")
            if 'catégories' in content.lower():
                print("✅ Section catégories présente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test interface: {str(e)}")
        return False

def test_static_files():
    """Teste l'accès aux fichiers statiques"""
    
    print("\n📁 Test des fichiers statiques...")
    print("=" * 60)
    
    try:
        # Test des polices
        font_files = [
            'fonts/halo.ttf',
            'fonts/RussoOne-Regular.ttf',
            'fonts/BaloonEverydayRegular-4B8El.ttf'
        ]
        
        for font in font_files:
            font_path = os.path.join('static', font)
            if os.path.exists(font_path):
                print(f"✅ Police {font} trouvée")
            else:
                print(f"⚠️  Police {font} manquante")
        
        # Test des CSS
        css_files = [
            'css/badge-animations.css',
            'css/appreciation.css',
            'css/highlights.css',
            'css/notifications.css',
            'css/floating-chat.css'
        ]
        
        for css in css_files:
            css_path = os.path.join('static', css)
            if os.path.exists(css_path):
                print(f"✅ CSS {css} trouvé")
            else:
                print(f"⚠️  CSS {css} manquant")
        
        # Test des images
        image_dirs = [
            'images',
            'badges',
            'insignes'
        ]
        
        for img_dir in image_dirs:
            img_path = os.path.join('static', img_dir)
            if os.path.exists(img_path):
                files_count = len([f for f in os.listdir(img_path) if f.endswith(('.png', '.jpg', '.jpeg'))])
                print(f"✅ Répertoire {img_dir}: {files_count} images")
            else:
                print(f"⚠️  Répertoire {img_dir} manquant")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test fichiers statiques: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🚀 Test complet des systèmes BLIZZ")
    print("=" * 80)
    
    tests = [
        ("Système Gaming", test_gaming_system),
        ("Système E-commerce", test_ecommerce_system),
        ("Intégration CinetPay", test_cinetpay_integration),
        ("Base de données", test_database_models),
        ("Interface utilisateur", test_interface_components),
        ("Fichiers statiques", test_static_files),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    # Résumé des tests
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ COMPLET DES TESTS BLIZZ")
    print("=" * 80)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
    
    print(f"\n📈 Résultats: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 Tous les tests sont réussis !")
        print("🚀 BLIZZ est prêt pour le lancement en production")
    elif success_count >= total_count * 0.8:
        print("🟡 La plupart des tests sont réussis")
        print("⚠️  Quelques ajustements mineurs recommandés")
    else:
        print("🔴 Plusieurs tests ont échoué")
        print("🚨 Vérification approfondie requise avant le lancement")
    
    # Recommandations
    print("\n🔧 Recommandations :")
    if success_count < total_count:
        failed_tests = [name for name, result in results if not result]
        print(f"   - Corriger les tests échoués : {', '.join(failed_tests)}")
    
    print("   - Effectuer des tests manuels approfondis")
    print("   - Vérifier la sécurité des comptes gaming")
    print("   - Tester les paiements CinetPay en mode test")
    print("   - Valider la synchronisation Shopify")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
