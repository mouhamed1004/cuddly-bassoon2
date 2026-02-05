#!/usr/bin/env python
"""
Script pour forcer le re-téléchargement des images d'un produit spécifique
et résoudre les problèmes de cache d'images
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

from django.core.files.base import ContentFile
from blizzgame.models import Product, ProductImage
from blizzgame.shopify_utils import _download_image_to_bytes
import requests
import time

def fix_product_images(product_slug):
    """Force le re-téléchargement des images d'un produit spécifique"""
    print(f"🔧 RÉPARATION DES IMAGES POUR LE PRODUIT: {product_slug}")
    print("=" * 60)
    
    try:
        # Trouver le produit
        product = Product.objects.get(slug=product_slug)
        print(f"✅ Produit trouvé: {product.name}")
        
        # Vérifier si c'est un produit Shopify
        if not product.shopify_product_id:
            print("❌ Ce produit n'est pas un produit Shopify")
            return False
        
        print(f"📦 ID Shopify: {product.shopify_product_id}")
        
        # Récupérer les données du produit depuis Shopify
        shopify_data = get_shopify_product_data(product.shopify_product_id)
        if not shopify_data:
            print("❌ Impossible de récupérer les données Shopify")
            return False
        
        print("✅ Données Shopify récupérées")
        
        # Supprimer les anciennes images
        print("🗑️ Suppression des anciennes images...")
        old_images = product.images.all()
        for img in old_images:
            try:
                if img.image:
                    img.image.delete(save=False)
                img.delete()
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression de l'image: {e}")
        
        # Supprimer l'image principale si elle existe
        if product.featured_image:
            try:
                product.featured_image.delete(save=False)
                product.featured_image = None
                product.save()
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression de l'image principale: {e}")
        
        print("✅ Anciennes images supprimées")
        
        # Re-télécharger les images avec les bonnes dimensions
        print("📥 Re-téléchargement des images...")
        images = shopify_data.get('images', [])
        if not images:
            print("❌ Aucune image trouvée dans les données Shopify")
            return False
        
        success_count = 0
        for idx, img_data in enumerate(images):
            src = img_data.get('src')
            if not src:
                continue
            
            print(f"📷 Téléchargement de l'image {idx + 1}/{len(images)}: {src}")
            
            # Forcer le téléchargement avec les dimensions originales
            # Ajouter des paramètres pour forcer les dimensions maximales
            if '?' in src:
                src += '&width=800&height=800&fit=contain'
            else:
                src += '?width=800&height=800&fit=contain'
            
            try:
                downloaded = _download_image_to_bytes(src)
                if not downloaded:
                    print(f"❌ Échec du téléchargement de l'image {idx + 1}")
                    continue
                
                filename, raw_bytes = downloaded
                
                # Créer la nouvelle image
                new_image = ProductImage(
                    product=product,
                    order=idx,
                    alt_text=img_data.get('alt', f'Image {idx + 1} de {product.name}')
                )
                new_image.image.save(filename, ContentFile(raw_bytes), save=True)
                
                # Définir la première image comme image principale
                if idx == 0:
                    product.featured_image.save(filename, ContentFile(raw_bytes), save=True)
                
                success_count += 1
                print(f"✅ Image {idx + 1} téléchargée et sauvegardée")
                
                # Petite pause pour éviter de surcharger Shopify
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Erreur lors du téléchargement de l'image {idx + 1}: {e}")
                continue
        
        print(f"✅ {success_count}/{len(images)} images re-téléchargées avec succès")
        
        # Sauvegarder le produit
        product.save()
        print("✅ Produit sauvegardé")
        
        return True
        
    except Product.DoesNotExist:
        print(f"❌ Produit non trouvé: {product_slug}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_shopify_product_data(product_id):
    """Récupère les données d'un produit depuis Shopify"""
    try:
        # Configuration Shopify (à adapter selon votre configuration)
        shopify_domain = "your-shop.myshopify.com"  # À remplacer
        access_token = "your-access-token"  # À remplacer
        
        url = f"https://{shopify_domain}/admin/api/2023-10/products/{product_id}.json"
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('product', {})
        else:
            print(f"❌ Erreur Shopify API: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des données Shopify: {e}")
        return None

def list_products_with_small_images():
    """Liste les produits qui pourraient avoir des problèmes d'images"""
    print("🔍 RECHERCHE DE PRODUITS AVEC DES PROBLÈMES D'IMAGES")
    print("=" * 60)
    
    products = Product.objects.filter(status='active').prefetch_related('images')
    
    problematic_products = []
    
    for product in products:
        images = product.images.all()
        if not images:
            continue
        
        # Vérifier si les images sont très petites
        small_images = []
        for img in images:
            if img.image:
                try:
                    # Vérifier la taille du fichier
                    file_size = img.image.size
                    if file_size < 10000:  # Moins de 10KB
                        small_images.append(img)
                except:
                    pass
        
        if small_images:
            problematic_products.append({
                'product': product,
                'small_images': small_images
            })
    
    if problematic_products:
        print(f"⚠️ {len(problematic_products)} produits avec des images potentiellement problématiques:")
        for item in problematic_products:
            product = item['product']
            small_count = len(item['small_images'])
            print(f"   • {product.name} (slug: {product.slug}) - {small_count} images petites")
    else:
        print("✅ Aucun produit avec des images problématiques détecté")
    
    return problematic_products

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage: python fix_product_images.py <product_slug>")
        print("   ou: python fix_product_images.py --list")
        return
    
    if sys.argv[1] == "--list":
        list_products_with_small_images()
        return
    
    product_slug = sys.argv[1]
    success = fix_product_images(product_slug)
    
    if success:
        print("\n🎉 RÉPARATION TERMINÉE AVEC SUCCÈS !")
        print("Les images du produit ont été re-téléchargées avec les bonnes dimensions.")
        print("Videz le cache de votre navigateur pour voir les changements.")
    else:
        print("\n❌ RÉPARATION ÉCHOUÉE")
        print("Vérifiez les logs ci-dessus pour plus de détails.")

if __name__ == "__main__":
    main()
