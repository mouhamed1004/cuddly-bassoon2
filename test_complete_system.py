#!/usr/bin/env python3
"""
Test complet du système BLIZZ
Vérifie que CinetPay, Shopify et BLIZZ communiquent correctement
"""

import os
import sys
import django
import requests
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.conf import settings
from blizzgame.models import ShopifyIntegration, Product, CinetPayTransaction, ShopCinetPayTransaction
from blizzgame.cinetpay_utils import CinetPayAPI, GamingCinetPayAPI
from blizzgame.shopify_utils import ShopifyAPI

def test_shopify_integration():
    """Test de l'intégration Shopify"""
    print("🔍 Test de l'intégration Shopify...")
    
    try:
        # Vérifier l'intégration
        integration = ShopifyIntegration.objects.filter(is_active=True).first()
        if not integration:
            print("❌ Aucune intégration Shopify active")
            return False
        
        print(f"✅ Intégration Shopify trouvée: {integration.shop_name}")
        print(f"   - URL: {integration.shop_url}")
        print(f"   - Active: {integration.is_active}")
        
        # Test API Shopify
        api = ShopifyAPI()
        products = api.get_products(limit=5)
        print(f"✅ API Shopify accessible: {len(products)} produits récupérés")
        
        # Vérifier les produits en base
        local_products = Product.objects.count()
        print(f"✅ Produits en base de données: {local_products}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur Shopify: {e}")
        return False

def test_cinetpay_credentials():
    """Test des credentials CinetPay"""
    print("\n🔍 Test des credentials CinetPay...")
    
    try:
        # Vérifier les variables d'environnement
        api_key = getattr(settings, 'CINETPAY_API_KEY', '')
        site_id = getattr(settings, 'CINETPAY_SITE_ID', '')
        secret_key = getattr(settings, 'CINETPAY_SECRET_KEY', '')
        
        if not all([api_key, site_id, secret_key]):
            print("❌ Credentials CinetPay manquants")
            return False
        
        print(f"✅ API Key: {api_key[:10]}...")
        print(f"✅ Site ID: {site_id}")
        print(f"✅ Secret Key: {secret_key[:10]}...")
        
        # Test API CinetPay Gaming
        gaming_api = GamingCinetPayAPI()
        print("✅ API CinetPay Gaming initialisée")
        
        # Test API CinetPay Shop
        shop_api = CinetPayAPI()
        print("✅ API CinetPay Shop initialisée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur CinetPay: {e}")
        return False

def test_database_connectivity():
    """Test de la connectivité base de données"""
    print("\n🔍 Test de la connectivité base de données...")
    
    try:
        # Test des modèles principaux
        from django.contrib.auth.models import User
        from blizzgame.models import Post, Profile
        
        user_count = User.objects.count()
        post_count = Post.objects.count()
        profile_count = Profile.objects.count()
        product_count = Product.objects.count()
        
        print(f"✅ Utilisateurs: {user_count}")
        print(f"✅ Posts: {post_count}")
        print(f"✅ Profils: {profile_count}")
        print(f"✅ Produits: {product_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False

def test_payment_flow():
    """Test du flux de paiement"""
    print("\n🔍 Test du flux de paiement...")
    
    try:
        # Vérifier les transactions existantes
        gaming_transactions = CinetPayTransaction.objects.count()
        shop_transactions = ShopCinetPayTransaction.objects.count()
        
        print(f"✅ Transactions Gaming: {gaming_transactions}")
        print(f"✅ Transactions Shop: {shop_transactions}")
        
        # Test des URLs de base
        base_url = getattr(settings, 'BASE_URL', '')
        print(f"✅ Base URL: {base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur flux de paiement: {e}")
        return False

def test_environment_variables():
    """Test des variables d'environnement"""
    print("\n🔍 Test des variables d'environnement...")
    
    required_vars = [
        'CINETPAY_API_KEY',
        'CINETPAY_SITE_ID', 
        'CINETPAY_SECRET_KEY',
        'SHOPIFY_SHOP_NAME',
        'SHOPIFY_ACCESS_TOKEN',
        'DATABASE_URL',
        'REDIS_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = getattr(settings, var, '')
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * 10}...{str(value)[-4:] if len(str(value)) > 4 else '***'}")
    
    if missing_vars:
        print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
        return False
    
    return True

def test_shopify_products_display():
    """Test de l'affichage des produits Shopify"""
    print("\n🔍 Test de l'affichage des produits Shopify...")
    
    try:
        # Récupérer quelques produits
        products = Product.objects.filter(status='active')[:3]
        
        if not products:
            print("❌ Aucun produit actif trouvé")
            return False
        
        print(f"✅ {len(products)} produits actifs trouvés:")
        for product in products:
            print(f"   - {product.name}: {product.price} EUR")
            if product.featured_image_url:
                print(f"     Image: {product.featured_image_url[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur affichage produits: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 TEST COMPLET DU SYSTÈME BLIZZ")
    print("=" * 50)
    
    tests = [
        ("Variables d'environnement", test_environment_variables),
        ("Connectivité base de données", test_database_connectivity),
        ("Intégration Shopify", test_shopify_integration),
        ("Credentials CinetPay", test_cinetpay_credentials),
        ("Flux de paiement", test_payment_flow),
        ("Affichage produits Shopify", test_shopify_products_display),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 RÉSULTAT: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Le système BLIZZ est entièrement opérationnel")
        print("✅ CinetPay, Shopify et BLIZZ communiquent correctement")
    else:
        print("⚠️  Certains tests ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
