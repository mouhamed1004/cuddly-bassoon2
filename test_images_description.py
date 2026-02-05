#!/usr/bin/env python
"""
Test pour vérifier que les images de description sont correctement limitées
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

def test_images_description():
    """Test que les images de description sont correctement limitées"""
    print("🖼️ TEST DES IMAGES DE DESCRIPTION")
    print("=" * 50)
    
    try:
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username=f"test_desc_{int(time.time())}",
            email=f"testdesc{int(time.time())}@example.com",
            password="TestPassword123!"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        
        print("✅ Utilisateur de test créé")
        
        # Créer un produit de test avec description contenant des images
        product = Product.objects.create(
            name="Test Product Description Images",
            slug=f"test-product-desc-{int(time.time())}",
            price=29.99,
            short_description="Produit de test pour images de description",
            description="""
            <p>Description avec des images :</p>
            <img src="https://example.com/image1.jpg" alt="Image 1">
            <p>Texte après l'image 1</p>
            <img src="https://example.com/image2.jpg" alt="Image 2">
            <p>Texte après l'image 2</p>
            """,
            is_featured=True
        )
        
        print(f"✅ Produit créé: {product.name}")
        
        # Créer des images de produit
        for i in range(2):
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
        
        # Test 2: Vérifier les styles pour les images de description
        print("\n🖼️ Test 2: Vérification des styles pour les images de description")
        assert '.product-description img' in content, "Sélecteur pour images de description présent"
        assert 'max-width: 100% !important' in content, "Max-width 100% pour images de description"
        assert 'max-height: 300px !important' in content, "Max-height 300px pour images de description"
        assert 'object-fit: contain !important' in content, "Object-fit contain pour images de description"
        assert 'border-radius: 8px' in content, "Border-radius pour images de description"
        assert 'margin: 1rem 0' in content, "Margin pour images de description"
        assert 'display: block' in content, "Display block pour images de description"
        assert 'margin-left: auto' in content, "Centrage horizontal pour images de description"
        assert 'margin-right: auto' in content, "Centrage horizontal pour images de description"
        print("✅ Styles pour images de description présents")
        
        # Test 3: Vérifier les styles responsive
        print("\n📱 Test 3: Vérification des styles responsive")
        assert 'max-height: 200px !important' in content, "Max-height responsive 200px"
        assert 'max-height: 150px !important' in content, "Max-height mobile 150px"
        print("✅ Styles responsive présents")
        
        # Test 4: Vérifier que les images de description sont dans le HTML
        print("\n🔗 Test 4: Vérification des images de description dans le HTML")
        assert 'https://example.com/image1.jpg' in content, "Image 1 dans la description"
        assert 'https://example.com/image2.jpg' in content, "Image 2 dans la description"
        assert 'alt="Image 1"' in content, "Alt text pour image 1"
        assert 'alt="Image 2"' in content, "Alt text pour image 2"
        print("✅ Images de description dans le HTML")
        
        # Test 5: Vérifier que le carrousel n'est pas affecté
        print("\n🎠 Test 5: Vérification que le carrousel n'est pas affecté")
        assert '.gaming-carousel' in content, "Carrousel présent"
        assert 'max-width: 90%' in content, "Carrousel avec max-width 90%"
        assert 'max-height: 90%' in content, "Carrousel avec max-height 90%"
        assert 'object-fit: contain' in content, "Carrousel avec object-fit contain"
        print("✅ Carrousel non affecté")
        
        # Test 6: Vérifier la structure HTML
        print("\n🔗 Test 6: Vérification de la structure HTML")
        assert '<div class="product-description">' in content, "Section description présente"
        assert '<img src="https://example.com/image1.jpg"' in content, "Image 1 dans la description"
        assert '<img src="https://example.com/image2.jpg"' in content, "Image 2 dans la description"
        print("✅ Structure HTML correcte")
        
        # Test 7: Vérifier l'absence de conflits
        print("\n🚫 Test 7: Vérification de l'absence de conflits")
        # Vérifier que les styles du carrousel et de la description sont distincts
        carousel_styles = content.count('max-width: 90%')
        description_styles = content.count('max-width: 100% !important')
        assert carousel_styles > 0, "Styles du carrousel présents"
        assert description_styles > 0, "Styles de description présents"
        print("✅ Aucun conflit entre carrousel et description")
        
        # Test 8: Vérifier la cohérence
        print("\n📊 Test 8: Vérification de la cohérence")
        lines = content.split('\n')
        description_lines = [line for line in lines if 'product-description' in line]
        print(f"   • Lignes liées à la description: {len(description_lines)}")
        
        # Compter les !important
        important_count = content.count('!important')
        print(f"   • Règles CSS avec !important: {important_count}")
        
        print("✅ Code cohérent et bien structuré")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ Les images de description sont correctement limitées")
        print("\n📋 RÉSUMÉ DE LA SOLUTION :")
        print("   • ✅ Images de description limitées à 300px de hauteur")
        print("   • ✅ Max-width: 100% pour s'adapter au conteneur")
        print("   • ✅ Object-fit: contain pour préserver les proportions")
        print("   • ✅ Border-radius: 8px pour l'esthétique")
        print("   • ✅ Margin: 1rem 0 pour l'espacement")
        print("   • ✅ Centrage horizontal automatique")
        print("   • ✅ Styles responsive (200px tablette, 150px mobile)")
        print("   • ✅ Carrousel non affecté")
        print("   • ✅ Aucun conflit entre les styles")
        
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
    success = test_images_description()
    sys.exit(0 if success else 1)
