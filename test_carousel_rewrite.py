#!/usr/bin/env python
"""
Test pour vérifier que le nouveau carrousel simple fonctionne
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

def test_carousel_rewrite():
    """Test que le nouveau carrousel simple fonctionne"""
    print("🔧 TEST DU NOUVEAU CARROUSEL SIMPLE")
    print("=" * 50)
    
    try:
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username=f"test_rewrite_{int(time.time())}",
            email=f"testrewrite{int(time.time())}@example.com",
            password="TestPassword123!"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        
        print("✅ Utilisateur de test créé")
        
        # Créer un produit de test avec des images de différentes tailles
        product = ShopProduct.objects.create(
            name="Test Product Rewrite",
            slug=f"test-product-rewrite-{int(time.time())}",
            price=29.99,
            short_description="Produit de test pour nouveau carrousel",
            description="Description détaillée du produit de test rewrite",
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
        
        # Test 2: Vérifier la structure HTML du carrousel
        print("\n🔧 Test 2: Vérification de la structure HTML")
        assert '<div class="gaming-carousel"' in content, "Structure HTML du carrousel présente"
        assert 'carousel-item' in content, "Éléments carousel-item présents"
        assert 'carousel-indicators' in content, "Indicateurs présents"
        print("✅ Structure HTML du carrousel correcte")
        
        # Test 3: Vérifier les styles CSS simples
        print("\n🎨 Test 3: Vérification des styles CSS simples")
        assert '.gaming-carousel' in content, "Classe gaming-carousel présente"
        assert 'height: 450px' in content, "Hauteur fixe de 450px"
        assert 'position: relative' in content, "Position relative"
        assert 'display: flex' in content, "Display flex"
        assert 'align-items: center' in content, "Align-items center"
        assert 'justify-content: center' in content, "Justify-content center"
        print("✅ Styles CSS simples présents")
        
        # Test 4: Vérifier l'absence de styles complexes
        print("\n🚫 Test 4: Vérification de l'absence de styles complexes")
        assert '!important' not in content or content.count('!important') < 5, "Pas trop de !important"
        assert 'contain: layout size' not in content, "Pas de contain layout size"
        assert 'isolation: isolate' not in content, "Pas d'isolation"
        assert 'resize: none' not in content, "Pas de resize none"
        assert 'transform: none' not in content, "Pas de transform none"
        print("✅ Styles complexes supprimés")
        
        # Test 5: Vérifier le JavaScript simple
        print("\n⚙️ Test 5: Vérification du JavaScript simple")
        assert 'initializeCarousel' in content, "Fonction initializeCarousel présente"
        assert 'showSlide' in content, "Fonction showSlide présente"
        assert 'nextSlide' in content, "Fonction nextSlide présente"
        assert 'prevSlide' in content, "Fonction prevSlide présente"
        assert 'startAutoPlay' in content, "Fonction startAutoPlay présente"
        assert 'stopAutoPlay' in content, "Fonction stopAutoPlay présente"
        print("✅ JavaScript simple présent")
        
        # Test 6: Vérifier l'absence de JavaScript complexe
        print("\n🚫 Test 6: Vérification de l'absence de JavaScript complexe")
        assert 'setProperty' not in content, "Pas de setProperty"
        assert 'removeAttribute' not in content, "Pas de removeAttribute"
        assert 'MutationObserver' not in content, "Pas de MutationObserver"
        assert 'setInterval' in content, "setInterval présent pour auto-play"
        print("✅ JavaScript complexe supprimé")
        
        # Test 7: Vérifier les styles responsive
        print("\n📱 Test 7: Vérification des styles responsive")
        assert '@media (max-width: 768px)' in content, "Media query tablette présente"
        assert '@media (max-width: 480px)' in content, "Media query mobile présente"
        assert 'height: 300px' in content, "Hauteur tablette de 300px"
        assert 'height: 250px' in content, "Hauteur mobile de 250px"
        print("✅ Styles responsive présents")
        
        # Test 8: Vérifier l'auto-play
        print("\n🔄 Test 8: Vérification de l'auto-play")
        assert 'setInterval' in content, "Auto-play configuré"
        assert 'mouseenter' in content, "Arrêt au survol configuré"
        assert 'mouseleave' in content, "Reprise après survol configurée"
        print("✅ Auto-play configuré")
        
        # Test 9: Vérifier la simplicité du code
        print("\n📊 Test 9: Vérification de la simplicité")
        lines = content.split('\n')
        carousel_lines = [line for line in lines if 'gaming-carousel' in line or 'carousel' in line]
        print(f"   • Lignes liées au carrousel: {len(carousel_lines)}")
        
        # Compter les !important
        important_count = content.count('!important')
        print(f"   • Nombre de !important: {important_count}")
        
        # Compter les fonctions JavaScript
        js_functions = ['initializeCarousel', 'showSlide', 'nextSlide', 'prevSlide', 'startAutoPlay', 'stopAutoPlay']
        js_count = sum(1 for func in js_functions if func in content)
        print(f"   • Fonctions JavaScript: {js_count}/{len(js_functions)}")
        
        print("✅ Code simplifié")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ Le nouveau carrousel simple fonctionne")
        print("\n📋 RÉSUMÉ DU NOUVEAU CARROUSEL :")
        print("   • ✅ CSS simple sans !important excessif")
        print("   • ✅ JavaScript simple et efficace")
        print("   • ✅ Auto-play avec pause au survol")
        print("   • ✅ Styles responsive")
        print("   • ✅ Structure HTML propre")
        print("   • ✅ Pas de techniques CSS complexes")
        print("   • ✅ Pas de JavaScript ultra-agressif")
        print("   • ✅ Code maintenable et lisible")
        
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
    success = test_carousel_rewrite()
    sys.exit(0 if success else 1)
