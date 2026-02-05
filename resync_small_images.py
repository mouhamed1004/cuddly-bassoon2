#!/usr/bin/env python
"""
Script simple pour re-synchroniser les produits avec des images minuscules
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

from blizzgame.models import Product, ProductImage
from blizzgame.shopify_utils import sync_products_from_shopify
import time

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
            print(f"     Shopify ID: {product.shopify_product_id}")
            print(f"     Images minuscules: {small_count}")
            print(f"     Taille totale: {total_size} bytes")
            print()
    else:
        print("✅ Aucun produit avec des images minuscules détecté")
    
    return problematic_products

def resync_specific_products(product_slugs):
    """Re-synchronise des produits spécifiques"""
    print(f"🔄 RE-SYNCHRONISATION DE {len(product_slugs)} PRODUITS")
    print("=" * 50)
    
    success_count = 0
    
    for slug in product_slugs:
        try:
            product = Product.objects.get(slug=slug)
            print(f"\n📦 Re-synchronisation de: {product.name}")
            print(f"   Slug: {product.slug}")
            print(f"   Shopify ID: {product.shopify_product_id}")
            
            if not product.shopify_product_id:
                print("   ❌ Ce produit n'est pas un produit Shopify")
                continue
            
            # Supprimer les anciennes images
            print("   🗑️ Suppression des anciennes images...")
            old_images = product.images.all()
            for img in old_images:
                try:
                    if img.image:
                        img.image.delete(save=False)
                    img.delete()
                except Exception as e:
                    print(f"   ⚠️ Erreur lors de la suppression: {e}")
            
            # Supprimer l'image principale
            if product.featured_image:
                try:
                    product.featured_image.delete(save=False)
                    product.featured_image = None
                    product.save()
                except Exception as e:
                    print(f"   ⚠️ Erreur lors de la suppression de l'image principale: {e}")
            
            print("   ✅ Anciennes images supprimées")
            
            # Marquer le produit pour re-synchronisation
            # En modifiant updated_at, le produit sera re-synchronisé lors de la prochaine sync
            from django.utils import timezone
            product.updated_at = timezone.now()
            product.save()
            
            print("   ✅ Produit marqué pour re-synchronisation")
            success_count += 1
            
        except Product.DoesNotExist:
            print(f"   ❌ Produit non trouvé: {slug}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print(f"\n✅ {success_count}/{len(product_slugs)} produits marqués pour re-synchronisation")
    return success_count

def resync_all_small_images():
    """Re-synchronise tous les produits avec des images minuscules"""
    print("🔄 RE-SYNCHRONISATION DE TOUS LES PRODUITS AVEC DES IMAGES MINUSCULES")
    print("=" * 70)
    
    problematic_products = find_products_with_small_images()
    
    if not problematic_products:
        print("✅ Aucun produit à re-synchroniser")
        return True
    
    # Extraire les slugs des produits problématiques
    product_slugs = [item['product'].slug for item in problematic_products]
    
    print(f"\n🔄 Re-synchronisation de {len(product_slugs)} produits...")
    
    success_count = resync_specific_products(product_slugs)
    
    if success_count > 0:
        print(f"\n🔄 Lancement de la synchronisation Shopify...")
        try:
            # Lancer la synchronisation Shopify
            synced_count = sync_products_from_shopify()
            print(f"✅ Synchronisation terminée: {synced_count} produits traités")
        except Exception as e:
            print(f"❌ Erreur lors de la synchronisation: {e}")
            print("💡 Vous pouvez lancer manuellement: python manage.py sync_shopify")
    
    return success_count > 0

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python resync_small_images.py --list")
        print("  python resync_small_images.py --resync-all")
        print("  python resync_small_images.py <product_slug1> <product_slug2> ...")
        return
    
    if sys.argv[1] == "--list":
        find_products_with_small_images()
    elif sys.argv[1] == "--resync-all":
        success = resync_all_small_images()
        if success:
            print("\n🎉 RE-SYNCHRONISATION TERMINÉE !")
            print("Les produits ont été marqués pour re-synchronisation.")
            print("Les nouvelles images seront téléchargées avec les bonnes dimensions.")
        else:
            print("\n❌ RE-SYNCHRONISATION ÉCHOUÉE")
    else:
        product_slugs = sys.argv[1:]
        success_count = resync_specific_products(product_slugs)
        
        if success_count > 0:
            print(f"\n🎉 {success_count} PRODUITS MARQUÉS POUR RE-SYNCHRONISATION !")
            print("Lancez la synchronisation Shopify pour télécharger les nouvelles images:")
            print("python manage.py sync_shopify")
        else:
            print("\n❌ AUCUN PRODUIT TRAITÉ")

if __name__ == "__main__":
    main()
