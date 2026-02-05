#!/usr/bin/env python
"""
Script pour identifier et réparer tous les produits avec des images minuscules
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
import requests
import time
from PIL import Image
import io

def find_products_with_small_images():
    """Trouve tous les produits avec des images minuscules"""
    print("🔍 RECHERCHE DE PRODUITS AVEC DES IMAGES MINUSCULES")
    print("=" * 60)
    
    products = Product.objects.filter(status='active').prefetch_related('images')
    problematic_products = []
    
    for product in products:
        images = product.images.all()
        if not images:
            continue
        
        small_images = []
        for img in images:
            if img.image:
                try:
                    # Vérifier la taille du fichier
                    file_size = img.image.size
                    if file_size < 50000:  # Moins de 50KB
                        small_images.append({
                            'image': img,
                            'size': file_size
                        })
                except:
                    pass
        
        if small_images:
            problematic_products.append({
                'product': product,
                'small_images': small_images
            })
    
    if problematic_products:
        print(f"⚠️ {len(problematic_products)} produits avec des images minuscules:")
        for item in problematic_products:
            product = item['product']
            small_count = len(item['small_images'])
            total_size = sum(img['size'] for img in item['small_images'])
            print(f"   • {product.name}")
            print(f"     Slug: {product.slug}")
            print(f"     Images minuscules: {small_count}")
            print(f"     Taille totale: {total_size} bytes")
            print()
    else:
        print("✅ Aucun produit avec des images minuscules détecté")
    
    return problematic_products

def fix_product_images_with_shopify_params(product_slug):
    """Répare les images d'un produit en forçant les dimensions Shopify"""
    print(f"🔧 RÉPARATION DES IMAGES POUR: {product_slug}")
    print("=" * 50)
    
    try:
        # Trouver le produit
        product = Product.objects.get(slug=product_slug)
        print(f"✅ Produit trouvé: {product.name}")
        
        if not product.shopify_product_id:
            print("❌ Ce produit n'est pas un produit Shopify")
            return False
        
        # Supprimer les anciennes images
        print("🗑️ Suppression des anciennes images...")
        old_images = product.images.all()
        for img in old_images:
            try:
                if img.image:
                    img.image.delete(save=False)
                img.delete()
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression: {e}")
        
        # Supprimer l'image principale
        if product.featured_image:
            try:
                product.featured_image.delete(save=False)
                product.featured_image = None
                product.save()
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression de l'image principale: {e}")
        
        print("✅ Anciennes images supprimées")
        
        # Re-télécharger depuis Shopify avec des dimensions forcées
        print("📥 Re-téléchargement depuis Shopify avec dimensions forcées...")
        success = re_download_with_forced_dimensions(product)
        
        if success:
            print("✅ Images re-téléchargées avec succès")
            return True
        else:
            print("❌ Échec du re-téléchargement")
            return False
        
    except Product.DoesNotExist:
        print(f"❌ Produit non trouvé: {product_slug}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def re_download_with_forced_dimensions(product):
    """Re-télécharge les images avec des dimensions forcées"""
    try:
        # Configuration Shopify (à adapter selon votre configuration)
        # Ces valeurs doivent être configurées selon votre setup Shopify
        shopify_domain = "your-shop.myshopify.com"  # À remplacer
        access_token = "your-access-token"  # À remplacer
        
        if shopify_domain == "your-shop.myshopify.com":
            print("⚠️ Configuration Shopify non définie")
            print("💡 Pour utiliser cette fonction, configurez shopify_domain et access_token")
            return False
        
        url = f"https://{shopify_domain}/admin/api/2023-10/products/{product.shopify_product_id}.json"
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Erreur Shopify API: {response.status_code}")
            return False
        
        data = response.json()
        product_data = data.get('product', {})
        images = product_data.get('images', [])
        
        if not images:
            print("❌ Aucune image trouvée dans Shopify")
            return False
        
        print(f"📷 {len(images)} images trouvées dans Shopify")
        
        success_count = 0
        for idx, img_data in enumerate(images):
            src = img_data.get('src')
            if not src:
                continue
            
            print(f"📥 Téléchargement de l'image {idx + 1}/{len(images)}")
            
            # Forcer les dimensions avec les paramètres Shopify
            # Ces paramètres forcent Shopify à retourner des images plus grandes
            if '?' in src:
                src += '&width=800&height=800&fit=contain'
            else:
                src += '?width=800&height=800&fit=contain'
            
            try:
                # Télécharger l'image
                resp = requests.get(src, timeout=30)
                resp.raise_for_status()
                
                # Vérifier la taille de l'image téléchargée
                image_size = len(resp.content)
                print(f"   Taille téléchargée: {image_size} bytes")
                
                if image_size < 10000:  # Moins de 10KB
                    print(f"   ⚠️ Image encore trop petite, essai avec des dimensions plus grandes...")
                    # Essayer avec des dimensions encore plus grandes
                    if '?' in src:
                        src = src.replace('width=800&height=800', 'width=1200&height=1200')
                    else:
                        src += '?width=1200&height=1200&fit=contain'
                    
                    resp = requests.get(src, timeout=30)
                    resp.raise_for_status()
                    image_size = len(resp.content)
                    print(f"   Nouvelle taille: {image_size} bytes")
                
                # Créer le nom de fichier
                from urllib.parse import urlparse
                parsed = urlparse(src)
                base_name = os.path.basename(parsed.path)
                if not base_name:
                    base_name = f'image_{idx}.jpg'
                
                # Créer la nouvelle image
                new_image = ProductImage(
                    product=product,
                    order=idx,
                    alt_text=img_data.get('alt', f'Image {idx + 1} de {product.name}')
                )
                new_image.image.save(base_name, ContentFile(resp.content), save=True)
                
                # Définir la première image comme image principale
                if idx == 0:
                    product.featured_image.save(base_name, ContentFile(resp.content), save=True)
                
                success_count += 1
                print(f"   ✅ Image {idx + 1} sauvegardée ({image_size} bytes)")
                
                # Pause pour éviter de surcharger Shopify
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Erreur lors du téléchargement de l'image {idx + 1}: {e}")
                continue
        
        print(f"✅ {success_count}/{len(images)} images re-téléchargées avec succès")
        product.save()
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Erreur lors du re-téléchargement: {e}")
        return False

def fix_all_small_images():
    """Répare tous les produits avec des images minuscules"""
    print("🔧 RÉPARATION DE TOUS LES PRODUITS AVEC DES IMAGES MINUSCULES")
    print("=" * 70)
    
    problematic_products = find_products_with_small_images()
    
    if not problematic_products:
        print("✅ Aucun produit à réparer")
        return True
    
    print(f"\n🔧 Réparation de {len(problematic_products)} produits...")
    
    success_count = 0
    for item in problematic_products:
        product = item['product']
        print(f"\n📦 Réparation du produit: {product.name}")
        
        success = fix_product_images_with_shopify_params(product.slug)
        if success:
            success_count += 1
            print(f"✅ {product.name} réparé avec succès")
        else:
            print(f"❌ Échec de la réparation de {product.name}")
        
        # Pause entre les produits
        time.sleep(2)
    
    print(f"\n🎉 RÉPARATION TERMINÉE: {success_count}/{len(problematic_products)} produits réparés")
    return success_count == len(problematic_products)

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_all_small_images.py --list")
        print("  python fix_all_small_images.py --fix-all")
        print("  python fix_all_small_images.py <product_slug>")
        return
    
    if sys.argv[1] == "--list":
        find_products_with_small_images()
    elif sys.argv[1] == "--fix-all":
        fix_all_small_images()
    else:
        product_slug = sys.argv[1]
        success = fix_product_images_with_shopify_params(product_slug)
        
        if success:
            print("\n🎉 RÉPARATION TERMINÉE AVEC SUCCÈS !")
            print("Les images du produit ont été re-téléchargées avec les bonnes dimensions.")
            print("Videz le cache de votre navigateur pour voir les changements.")
        else:
            print("\n❌ RÉPARATION ÉCHOUÉE")
            print("Vérifiez les logs ci-dessus pour plus de détails.")

if __name__ == "__main__":
    main()
