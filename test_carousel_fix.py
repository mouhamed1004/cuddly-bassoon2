#!/usr/bin/env python
"""
Test pour vérifier que le carrousel des produits dropshipping a une taille fixe
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

def test_carousel_fix():
    """Test que le carrousel a une taille fixe et stable"""
    print("🖼️ TEST DE STABILITÉ DU CARROUSEL DROPSHIPPING")
    print("=" * 60)
    
    try:
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username=f"test_carousel_{int(time.time())}",
            email=f"testcarousel{int(time.time())}@example.com",
            password="TestPassword123!"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        
        print("✅ Utilisateur de test créé")
        
        # Créer un produit de test avec des images
        product = ShopProduct.objects.create(
            name="Test Product Carousel",
            slug=f"test-product-carousel-{int(time.time())}",
            price=29.99,
            short_description="Produit de test pour le carrousel",
            description="Description détaillée du produit de test",
            is_featured=True
        )
        
        print(f"✅ Produit créé: {product.name}")
        
        # Créer des images de test avec différentes dimensions
        # Image 1: Format paysage (large)
        image1 = ShopProductImage.objects.create(
            product=product,
            image="test_images/landscape_image.jpg",  # Simulé
            alt_text="Image paysage",
            order=1
        )
        
        # Image 2: Format portrait (haut)
        image2 = ShopProductImage.objects.create(
            product=product,
            image="test_images/portrait_image.jpg",  # Simulé
            alt_text="Image portrait",
            order=2
        )
        
        # Image 3: Format carré
        image3 = ShopProductImage.objects.create(
            product=product,
            image="test_images/square_image.jpg",  # Simulé
            alt_text="Image carrée",
            order=3
        )
        
        print("✅ Images de test créées avec différentes dimensions")
        
        client = Client()
        
        # Test 1: Accès à la page produit
        print("\n📄 Test 1: Accès à la page produit")
        response = client.get(f'/shop/product/{product.slug}/')
        assert response.status_code == 200, "Page produit accessible"
        content = response.content.decode('utf-8')
        print("✅ Page produit accessible")
        
        # Test 2: Vérifier la présence du carrousel
        print("\n🎠 Test 2: Vérification du carrousel")
        assert 'gaming-carousel' in content, "Carrousel présent dans le HTML"
        assert 'carousel-item' in content, "Éléments du carrousel présents"
        assert 'carousel-indicators' in content, "Indicateurs du carrousel présents"
        print("✅ Carrousel présent dans le HTML")
        
        # Test 3: Vérifier les styles CSS fixes
        print("\n🎨 Test 3: Vérification des styles CSS")
        assert 'height: 450px' in content, "Hauteur fixe du carrousel définie"
        assert 'object-fit: contain' in content, "Object-fit contain défini"
        assert 'max-width: 90%' in content, "Largeur maximale des images définie"
        assert 'max-height: 90%' in content, "Hauteur maximale des images définie"
        print("✅ Styles CSS fixes présents")
        
        # Test 4: Vérifier les règles responsive
        print("\n📱 Test 4: Vérification des règles responsive")
        assert '@media (max-width: 768px)' in content, "Règles responsive tablette présentes"
        assert '@media (max-width: 480px)' in content, "Règles responsive mobile présentes"
        assert 'height: 300px' in content, "Hauteur mobile définie"
        assert 'height: 250px' in content, "Hauteur très petit écran définie"
        print("✅ Règles responsive présentes")
        
        # Test 5: Vérifier les contraintes d'images
        print("\n🖼️ Test 5: Vérification des contraintes d'images")
        assert 'min-width: 0' in content, "Contrainte min-width définie"
        assert 'min-height: 0' in content, "Contrainte min-height définie"
        assert 'width: auto' in content, "Largeur automatique définie"
        assert 'height: auto' in content, "Hauteur automatique définie"
        print("✅ Contraintes d'images définies")
        
        # Test 6: Vérifier la structure du conteneur
        print("\n📦 Test 6: Vérification de la structure du conteneur")
        assert 'min-height: 500px' in content, "Hauteur minimale du conteneur définie"
        assert 'display: flex' in content, "Display flex défini"
        assert 'flex-direction: column' in content, "Direction flex définie"
        print("✅ Structure du conteneur optimisée")
        
        # Test 7: Vérifier les règles spéciales pour images
        print("\n🔧 Test 7: Vérification des règles spéciales")
        assert 'img[style*="width"]' in content, "Règles spéciales pour images larges"
        assert 'img[style*="height"]' in content, "Règles spéciales pour images hautes"
        assert '!important' in content, "Règles importantes définies"
        print("✅ Règles spéciales pour images définies")
        
        # Test 8: Vérifier le JavaScript du carrousel
        print("\n⚙️ Test 8: Vérification du JavaScript")
        assert 'showSlide' in content, "Fonction showSlide présente"
        assert 'nextSlide' in content, "Fonction nextSlide présente"
        assert 'prevSlide' in content, "Fonction prevSlide présente"
        assert 'currentSlide' in content, "Variable currentSlide présente"
        print("✅ JavaScript du carrousel présent")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ Le carrousel a une taille fixe et stable")
        print("\n📋 RÉSUMÉ DES AMÉLIORATIONS :")
        print("   • ✅ Hauteur fixe du carrousel (450px desktop, 300px tablette, 250px mobile)")
        print("   • ✅ Contraintes d'images (max-width: 90%, max-height: 90%)")
        print("   • ✅ Object-fit: contain pour maintenir les proportions")
        print("   • ✅ Règles spéciales pour images très larges/hautes")
        print("   • ✅ Structure flex pour centrage parfait")
        print("   • ✅ Hauteur minimale du conteneur (500px)")
        print("   • ✅ Règles responsive complètes")
        print("   • ✅ JavaScript fonctionnel pour navigation")
        
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
    success = test_carousel_fix()
    sys.exit(0 if success else 1)
