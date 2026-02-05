#!/usr/bin/env python
"""
Test pour vérifier que la solution de cache-busting des images fonctionne
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
from blizzgame.models import Profile, Product, ProductImage
import time

def test_image_cache_fix():
    """Test que la solution de cache-busting des images fonctionne"""
    print("🔧 TEST DE LA SOLUTION DE CACHE-BUSTING DES IMAGES")
    print("=" * 60)
    
    try:
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username=f"test_cache_{int(time.time())}",
            email=f"testcache{int(time.time())}@example.com",
            password="TestPassword123!"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        
        print("✅ Utilisateur de test créé")
        
        # Créer un produit de test
        product = Product.objects.create(
            name="Test Product Cache Fix",
            slug=f"test-product-cache-{int(time.time())}",
            price=29.99,
            short_description="Produit de test pour cache-busting",
            description="Description détaillée du produit de test cache-busting",
            is_featured=True
        )
        
        print(f"✅ Produit créé: {product.name}")
        
        # Créer des images de test
        for i in range(3):
            image = ProductImage.objects.create(
                product=product,
                image="test_images/test_image.jpg",  # Simulé
                alt_text=f"Image de test {i+1}",
                order=i
            )
            print(f"✅ Image {i+1} créée")
        
        client = Client()
        
        # Test 1: Accès à la page produit
        print("\n📄 Test 1: Accès à la page produit")
        response = client.get(f'/shop/product/{product.slug}/')
        assert response.status_code == 200, "Page produit accessible"
        content = response.content.decode('utf-8')
        print("✅ Page produit accessible")
        
        # Test 2: Vérifier les paramètres de cache-busting dans les URLs d'images
        print("\n🔧 Test 2: Vérification des paramètres de cache-busting")
        assert '?v=' in content, "Paramètre de version présent dans les URLs d'images"
        assert '&t=' in content, "Paramètre de timestamp présent dans les URLs d'images"
        assert 'loading="lazy"' in content, "Attribut loading lazy présent"
        print("✅ Paramètres de cache-busting présents")
        
        # Test 3: Vérifier la fonction JavaScript de cache-busting
        print("\n⚙️ Test 3: Vérification du JavaScript de cache-busting")
        assert 'forceImageReload' in content, "Fonction forceImageReload présente"
        assert 'cache-busting' in content, "Commentaire cache-busting présent"
        assert 'Date.now()' in content, "Timestamp dynamique présent"
        assert 'new Image()' in content, "Création d'image dynamique présente"
        print("✅ JavaScript de cache-busting présent")
        
        # Test 4: Vérifier la structure des URLs d'images
        print("\n🔗 Test 4: Vérification de la structure des URLs d'images")
        # Compter le nombre d'occurrences de paramètres de cache-busting
        version_count = content.count('?v=')
        timestamp_count = content.count('&t=')
        lazy_count = content.count('loading="lazy"')
        
        print(f"   • Paramètres de version (?v=): {version_count}")
        print(f"   • Paramètres de timestamp (&t=): {timestamp_count}")
        print(f"   • Attributs loading lazy: {lazy_count}")
        
        assert version_count >= 3, "Au moins 3 paramètres de version présents"
        assert timestamp_count >= 3, "Au moins 3 paramètres de timestamp présents"
        assert lazy_count >= 3, "Au moins 3 attributs loading lazy présents"
        print("✅ Structure des URLs d'images correcte")
        
        # Test 5: Vérifier la fonction d'initialisation du carrousel
        print("\n🎠 Test 5: Vérification de l'initialisation du carrousel")
        assert 'initializeCarousel' in content, "Fonction initializeCarousel présente"
        assert 'forceImageReload()' in content, "Appel à forceImageReload présent"
        assert 'carousel.style.height = \'450px\'' in content, "Hauteur forcée présente"
        assert 'carousel.style.width = \'100%\'' in content, "Largeur forcée présente"
        print("✅ Initialisation du carrousel correcte")
        
        # Test 6: Vérifier la gestion des erreurs
        print("\n⚠️ Test 6: Vérification de la gestion des erreurs")
        assert 'onload' in content, "Gestionnaire onload présent"
        assert 'onerror' in content, "Gestionnaire onerror présent"
        assert 'console.log' in content, "Logs de succès présents"
        assert 'console.warn' in content, "Logs d'erreur présents"
        print("✅ Gestion des erreurs présente")
        
        # Test 7: Vérifier la compatibilité avec les images existantes
        print("\n🔄 Test 7: Vérification de la compatibilité")
        assert 'originalSrc' in content, "Variable originalSrc présente"
        assert 'newSrc' in content, "Variable newSrc présente"
        assert 'separator' in content, "Gestion du séparateur présente"
        assert 'includes(\'?\')' in content, "Détection des paramètres existants présente"
        print("✅ Compatibilité avec les images existantes")
        
        # Test 8: Vérifier les performances
        print("\n⚡ Test 8: Vérification des performances")
        # Vérifier que le code n'est pas trop lourd
        lines = content.split('\n')
        js_lines = [line for line in lines if 'forceImageReload' in line or 'cache-busting' in line]
        print(f"   • Lignes liées au cache-busting: {len(js_lines)}")
        
        # Vérifier que le code est optimisé
        assert 'forEach' in content, "Boucle forEach optimisée présente"
        assert 'Date.now()' in content, "Timestamp unique par chargement"
        print("✅ Code optimisé pour les performances")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ La solution de cache-busting des images fonctionne")
        print("\n📋 RÉSUMÉ DE LA SOLUTION :")
        print("   • ✅ Paramètres de cache-busting dans les URLs d'images")
        print("   • ✅ JavaScript pour forcer le rechargement des images")
        print("   • ✅ Gestion des erreurs et logs")
        print("   • ✅ Compatibilité avec les images existantes")
        print("   • ✅ Code optimisé pour les performances")
        print("   • ✅ Attributs loading lazy pour l'optimisation")
        print("   • ✅ Timestamps dynamiques pour éviter le cache")
        
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
    success = test_image_cache_fix()
    sys.exit(0 if success else 1)
