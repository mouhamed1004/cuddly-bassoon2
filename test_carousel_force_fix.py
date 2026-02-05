#!/usr/bin/env python
"""
Test pour vérifier que les contraintes forcées du carrousel fonctionnent
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

def test_carousel_force_fix():
    """Test que les contraintes forcées du carrousel fonctionnent"""
    print("🔧 TEST DES CONTRAINTES FORCÉES DU CARROUSEL")
    print("=" * 60)
    
    try:
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username=f"test_force_{int(time.time())}",
            email=f"testforce{int(time.time())}@example.com",
            password="TestPassword123!"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        
        print("✅ Utilisateur de test créé")
        
        # Créer un produit de test avec des images de différentes tailles
        product = ShopProduct.objects.create(
            name="Test Product Force Fix",
            slug=f"test-product-force-fix-{int(time.time())}",
            price=29.99,
            short_description="Produit de test pour contraintes forcées",
            description="Description détaillée du produit de test",
            is_featured=True
        )
        
        print(f"✅ Produit créé: {product.name}")
        
        # Créer des images de test avec des dimensions très différentes
        # Image 1: Très petite (100x50)
        image1 = ShopProductImage.objects.create(
            product=product,
            image="test_images/tiny_image.jpg",  # Simulé
            alt_text="Image très petite",
            order=1
        )
        
        # Image 2: Très large (2000x100)
        image2 = ShopProductImage.objects.create(
            product=product,
            image="test_images/wide_image.jpg",  # Simulé
            alt_text="Image très large",
            order=2
        )
        
        # Image 3: Très haute (100x2000)
        image3 = ShopProductImage.objects.create(
            product=product,
            image="test_images/tall_image.jpg",  # Simulé
            alt_text="Image très haute",
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
        
        # Test 2: Vérifier les contraintes CSS forcées
        print("\n🔧 Test 2: Vérification des contraintes CSS forcées")
        assert 'height: 450px !important' in content, "Hauteur forcée avec !important"
        assert 'min-height: 450px !important' in content, "Min-height forcée avec !important"
        assert 'max-height: 450px !important' in content, "Max-height forcée avec !important"
        assert 'width: 100% !important' in content, "Largeur forcée avec !important"
        assert 'flex-shrink: 0 !important' in content, "Flex-shrink forcé avec !important"
        print("✅ Contraintes CSS forcées présentes")
        
        # Test 3: Vérifier les règles ultra-spécifiques
        print("\n🎯 Test 3: Vérification des règles ultra-spécifiques")
        assert '.product-images .gaming-carousel' in content, "Règle ultra-spécifique présente"
        assert '.gaming-carousel[style]' in content, "Override des styles inline présent"
        assert 'img[width]' in content, "Règle pour attribut width présent"
        assert 'img[height]' in content, "Règle pour attribut height présent"
        print("✅ Règles ultra-spécifiques présentes")
        
        # Test 4: Vérifier le JavaScript de forçage
        print("\n⚙️ Test 4: Vérification du JavaScript de forçage")
        assert 'enforceCarouselConstraints' in content, "Fonction de forçage présente"
        assert 'carousel.style.height = \'450px\'' in content, "Forçage JavaScript de la hauteur"
        assert 'carousel.style.minHeight = \'450px\'' in content, "Forçage JavaScript du min-height"
        assert 'carousel.style.maxHeight = \'450px\'' in content, "Forçage JavaScript du max-height"
        assert 'img.style.maxWidth = \'90%\'' in content, "Forçage JavaScript de la largeur max"
        assert 'img.style.maxHeight = \'90%\'' in content, "Forçage JavaScript de la hauteur max"
        print("✅ JavaScript de forçage présent")
        
        # Test 5: Vérifier l'observateur de mutations
        print("\n👁️ Test 5: Vérification de l'observateur de mutations")
        assert 'MutationObserver' in content, "MutationObserver présent"
        assert 'observer.observe' in content, "Observation du carrousel configurée"
        assert 'enforceCarouselConstraints' in content, "Réapplication des contraintes configurée"
        print("✅ Observateur de mutations configuré")
        
        # Test 6: Vérifier l'application des contraintes au chargement
        print("\n🚀 Test 6: Vérification de l'application au chargement")
        assert 'DOMContentLoaded' in content, "Événement DOMContentLoaded présent"
        assert 'carousel.style.height = \'450px\'' in content, "Application au chargement configurée"
        assert 'carousel.style.width = \'100%\'' in content, "Application de la largeur au chargement"
        print("✅ Application des contraintes au chargement configurée")
        
        # Test 7: Vérifier la réapplication lors des changements de slide
        print("\n🔄 Test 7: Vérification de la réapplication lors des changements")
        assert 'showSlide' in content, "Fonction showSlide présente"
        assert 'enforceCarouselConstraints()' in content, "Réapplication dans showSlide"
        assert 'nextSlide' in content, "Fonction nextSlide présente"
        assert 'prevSlide' in content, "Fonction prevSlide présente"
        print("✅ Réapplication lors des changements configurée")
        
        # Test 8: Vérifier les contraintes sur les images
        print("\n🖼️ Test 8: Vérification des contraintes sur les images")
        assert 'img.style.maxWidth = \'90%\'' in content, "Contrainte largeur max sur images"
        assert 'img.style.maxHeight = \'90%\'' in content, "Contrainte hauteur max sur images"
        assert 'img.style.width = \'auto\'' in content, "Largeur auto sur images"
        assert 'img.style.height = \'auto\'' in content, "Hauteur auto sur images"
        assert 'img.style.objectFit = \'contain\'' in content, "Object-fit contain sur images"
        print("✅ Contraintes sur les images configurées")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ Les contraintes forcées du carrousel sont implémentées")
        print("\n📋 RÉSUMÉ DES AMÉLIORATIONS FORCÉES :")
        print("   • ✅ CSS avec !important pour override complet")
        print("   • ✅ Règles ultra-spécifiques pour tous les cas")
        print("   • ✅ JavaScript de forçage au chargement")
        print("   • ✅ Réapplication automatique lors des changements")
        print("   • ✅ Observateur de mutations pour détecter les changements")
        print("   • ✅ Contraintes forcées sur toutes les images")
        print("   • ✅ Override des styles inline et attributs")
        print("   • ✅ Forçage de la taille du conteneur")
        
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
    success = test_carousel_force_fix()
    sys.exit(0 if success else 1)
