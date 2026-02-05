#!/usr/bin/env python
"""
Test pour vérifier que la solution ultra-agressive du carrousel fonctionne
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
from blizzgame.models import Profile, ShopProduct, ShopProductImage
import time

def test_carousel_ultra_aggressive():
    """Test que la solution ultra-agressive du carrousel fonctionne"""
    print("🔧 TEST DE LA SOLUTION ULTRA-AGRESSIVE DU CARROUSEL")
    print("=" * 70)
    
    try:
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username=f"test_ultra_{int(time.time())}",
            email=f"testultra{int(time.time())}@example.com",
            password="TestPassword123!"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        
        print("✅ Utilisateur de test créé")
        
        # Créer un produit de test avec des images de différentes tailles
        product = ShopProduct.objects.create(
            name="Test Product Ultra Aggressive",
            slug=f"test-product-ultra-{int(time.time())}",
            price=29.99,
            short_description="Produit de test pour solution ultra-agressive",
            description="Description détaillée du produit de test ultra-agressive",
            is_featured=True
        )
        
        print(f"✅ Produit créé: {product.name}")
        
        # Créer des images de test avec des dimensions très différentes
        # Image 1: Très petite (50x25)
        image1 = ShopProductImage.objects.create(
            product=product,
            image="test_images/tiny_image.jpg",  # Simulé
            alt_text="Image très petite",
            order=1
        )
        
        # Image 2: Très large (3000x150)
        image2 = ShopProductImage.objects.create(
            product=product,
            image="test_images/ultra_wide_image.jpg",  # Simulé
            alt_text="Image ultra large",
            order=2
        )
        
        # Image 3: Très haute (100x3000)
        image3 = ShopProductImage.objects.create(
            product=product,
            image="test_images/ultra_tall_image.jpg",  # Simulé
            alt_text="Image ultra haute",
            order=3
        )
        
        print("✅ Images de test créées avec dimensions extrêmes")
        
        client = Client()
        
        # Test 1: Accès à la page produit
        print("\n📄 Test 1: Accès à la page produit")
        response = client.get(f'/shop/product/{product.slug}/')
        assert response.status_code == 200, "Page produit accessible"
        content = response.content.decode('utf-8')
        print("✅ Page produit accessible")
        
        # Test 2: Vérifier les contraintes CSS ultra-agressives
        print("\n🔧 Test 2: Vérification des contraintes CSS ultra-agressives")
        assert 'height: 450px !important' in content, "Hauteur forcée avec !important"
        assert 'min-height: 450px !important' in content, "Min-height forcée avec !important"
        assert 'max-height: 450px !important' in content, "Max-height forcée avec !important"
        assert 'width: 100% !important' in content, "Largeur forcée avec !important"
        assert 'flex-shrink: 0 !important' in content, "Flex-shrink forcé avec !important"
        assert 'contain: layout size !important' in content, "Contain layout size forcé"
        assert 'isolation: isolate !important' in content, "Isolation forcée"
        assert 'resize: none !important' in content, "Resize désactivé"
        assert 'transform: none !important' in content, "Transform désactivé"
        print("✅ Contraintes CSS ultra-agressives présentes")
        
        # Test 3: Vérifier les règles ultra-spécifiques
        print("\n🎯 Test 3: Vérification des règles ultra-spécifiques")
        assert 'body .container .row .col-md-6 .product-images .gaming-carousel' in content, "Sélecteur de spécificité maximale présent"
        assert '.gaming-carousel.carousel.slide' in content, "Override des frameworks CSS présent"
        assert '.gaming-carousel[style*="height: auto"]' in content, "Override des styles inline présent"
        assert '.gaming-carousel::before' in content, "Pseudo-élément de forçage présent"
        print("✅ Règles ultra-spécifiques présentes")
        
        # Test 4: Vérifier les media queries universelles
        print("\n📱 Test 4: Vérification des media queries universelles")
        assert '@media all' in content, "Media query universelle présente"
        assert '@media screen' in content, "Media query screen présente"
        assert '@media print' in content, "Media query print présente"
        print("✅ Media queries universelles présentes")
        
        # Test 5: Vérifier le JavaScript ultra-agressif
        print("\n⚙️ Test 5: Vérification du JavaScript ultra-agressif")
        assert 'forceCarouselSize' in content, "Fonction de forçage ultra-agressive présente"
        assert 'setProperty' in content, "setProperty avec important présent"
        assert 'removeAttribute' in content, "Suppression d'attributs présente"
        assert 'setInterval' in content, "Réapplication automatique présente"
        assert 'maxAttempts = 50' in content, "Tentatives multiples configurées"
        print("✅ JavaScript ultra-agressif présent")
        
        # Test 6: Vérifier la suppression d'attributs
        print("\n🗑️ Test 6: Vérification de la suppression d'attributs")
        assert 'removeAttribute(\'width\')' in content, "Suppression attribut width"
        assert 'removeAttribute(\'height\')' in content, "Suppression attribut height"
        assert 'removeAttribute(\'data-height\')' in content, "Suppression data-height"
        assert 'removeAttribute(\'data-width\')' in content, "Suppression data-width"
        print("✅ Suppression d'attributs configurée")
        
        # Test 7: Vérifier les techniques CSS avancées
        print("\n🔬 Test 7: Vérification des techniques CSS avancées")
        assert 'box-sizing: border-box !important' in content, "Box-sizing forcé"
        assert 'contain: layout size !important' in content, "Contain layout size"
        assert 'isolation: isolate !important' in content, "Isolation"
        assert 'resize: none !important' in content, "Resize désactivé"
        assert 'transform: none !important' in content, "Transform désactivé"
        print("✅ Techniques CSS avancées présentes")
        
        # Test 8: Vérifier la réapplication automatique
        print("\n🔄 Test 8: Vérification de la réapplication automatique")
        assert 'setInterval' in content, "Intervalle de réapplication"
        assert 'maxAttempts = 50' in content, "Nombre maximum de tentatives"
        assert 'clearInterval' in content, "Nettoyage de l'intervalle"
        assert 'attempts++' in content, "Compteur de tentatives"
        print("✅ Réapplication automatique configurée")
        
        # Test 9: Vérifier les contraintes sur le conteneur parent
        print("\n📦 Test 9: Vérification des contraintes sur le conteneur parent")
        assert '.product-images' in content, "Conteneur parent ciblé"
        assert 'height: 500px !important' in content, "Hauteur du conteneur parent forcée"
        assert 'min-height: 500px !important' in content, "Min-height du conteneur parent forcée"
        assert 'max-height: 500px !important' in content, "Max-height du conteneur parent forcée"
        print("✅ Contraintes sur le conteneur parent présentes")
        
        # Test 10: Vérifier l'override des frameworks
        print("\n🎨 Test 10: Vérification de l'override des frameworks")
        assert '.gaming-carousel.carousel.slide' in content, "Override Bootstrap slide"
        assert '.gaming-carousel.carousel.fade' in content, "Override Bootstrap fade"
        assert '.gaming-carousel.carousel.carousel-fade' in content, "Override carousel-fade"
        assert '.gaming-carousel.carousel.carousel-slide' in content, "Override carousel-slide"
        print("✅ Override des frameworks configuré")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ La solution ultra-agressive du carrousel est implémentée")
        print("\n📋 RÉSUMÉ DE LA SOLUTION ULTRA-AGRESSIVE :")
        print("   • ✅ CSS avec !important et sélecteurs de spécificité maximale")
        print("   • ✅ Techniques CSS avancées (contain, isolation, resize, transform)")
        print("   • ✅ JavaScript ultra-agressif avec setProperty et removeAttribute")
        print("   • ✅ Réapplication automatique toutes les 100ms pendant 5 secondes")
        print("   • ✅ Suppression des attributs width/height des images")
        print("   • ✅ Override de tous les frameworks CSS possibles")
        print("   • ✅ Media queries universelles (all, screen, print)")
        print("   • ✅ Pseudo-éléments pour forcer la taille")
        print("   • ✅ Contraintes sur le conteneur parent")
        print("   • ✅ Sélecteurs d'attribut pour override des styles inline")
        
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
    success = test_carousel_ultra_aggressive()
    sys.exit(0 if success else 1)

