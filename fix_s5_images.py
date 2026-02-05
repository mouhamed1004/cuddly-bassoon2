#!/usr/bin/env python
"""
Script simple pour forcer le re-téléchargement des images du produit S5 mobile game console
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

def fix_s5_images():
    """Force le re-téléchargement des images du produit S5 mobile game console"""
    print("🔧 RÉPARATION DES IMAGES DU PRODUIT S5 MOBILE GAME CONSOLE")
    print("=" * 60)
    
    try:
        # Trouver le produit S5
        product = Product.objects.filter(
            name__icontains="S5 mobile game console"
        ).first()
        
        if not product:
            print("❌ Produit S5 mobile game console non trouvé")
            print("Recherche de produits similaires...")
            
            # Chercher des produits similaires
            similar_products = Product.objects.filter(
                name__icontains="S5"
            )
            
            if similar_products:
                print("Produits trouvés avec 'S5' dans le nom:")
                for p in similar_products:
                    print(f"   • {p.name} (slug: {p.slug})")
            else:
                print("Aucun produit avec 'S5' trouvé")
            
            return False
        
        print(f"✅ Produit trouvé: {product.name}")
        print(f"📦 Slug: {product.slug}")
        print(f"🆔 ID: {product.id}")
        
        # Vérifier les images actuelles
        images = product.images.all()
        print(f"📷 Nombre d'images actuelles: {images.count()}")
        
        if images.count() == 0:
            print("❌ Aucune image trouvée pour ce produit")
            return False
        
        # Afficher les informations sur les images actuelles
        for i, img in enumerate(images):
            print(f"   Image {i+1}: {img.image.name if img.image else 'Pas d\'image'}")
            if img.image:
                try:
                    file_size = img.image.size
                    print(f"      Taille: {file_size} bytes")
                except:
                    print(f"      Taille: Inconnue")
        
        # Supprimer les anciennes images
        print("\n🗑️ Suppression des anciennes images...")
        for img in images:
            try:
                if img.image:
                    img.image.delete(save=False)
                img.delete()
                print(f"   ✅ Image supprimée")
            except Exception as e:
                print(f"   ⚠️ Erreur lors de la suppression: {e}")
        
        # Supprimer l'image principale si elle existe
        if product.featured_image:
            try:
                product.featured_image.delete(save=False)
                product.featured_image = None
                product.save()
                print("   ✅ Image principale supprimée")
            except Exception as e:
                print(f"   ⚠️ Erreur lors de la suppression de l'image principale: {e}")
        
        print("✅ Anciennes images supprimées")
        
        # Si c'est un produit Shopify, essayer de re-télécharger
        if product.shopify_product_id:
            print(f"\n📥 Re-téléchargement depuis Shopify (ID: {product.shopify_product_id})...")
            success = re_download_from_shopify(product)
            if success:
                print("✅ Images re-téléchargées depuis Shopify")
            else:
                print("❌ Échec du re-téléchargement depuis Shopify")
                print("💡 Vous devrez peut-être re-synchroniser le produit depuis Shopify")
        else:
            print("❌ Ce produit n'est pas un produit Shopify")
            print("💡 Vous devrez ajouter manuellement de nouvelles images")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def re_download_from_shopify(product):
    """Tente de re-télécharger les images depuis Shopify"""
    try:
        # Ici, vous devriez implémenter la logique de re-téléchargement
        # depuis Shopify en utilisant l'API Shopify
        # Pour l'instant, on retourne False car cela nécessite une configuration Shopify
        
        print("⚠️ Re-téléchargement depuis Shopify non implémenté dans ce script")
        print("💡 Utilisez l'interface d'administration Django ou re-synchronisez depuis Shopify")
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors du re-téléchargement: {e}")
        return False

def clear_image_cache():
    """Efface le cache des images en forçant le rechargement"""
    print("🧹 NETTOYAGE DU CACHE DES IMAGES")
    print("=" * 40)
    
    # Cette fonction pourrait être étendue pour effacer le cache du serveur
    # Pour l'instant, on affiche juste des instructions
    
    print("Pour effacer le cache des images:")
    print("1. Videz le cache de votre navigateur (Ctrl+F5)")
    print("2. Redémarrez le serveur Django si nécessaire")
    print("3. Vérifiez que les images se rechargent correctement")
    
    return True

def main():
    """Fonction principale"""
    if len(sys.argv) > 1 and sys.argv[1] == "--clear-cache":
        clear_image_cache()
        return
    
    success = fix_s5_images()
    
    if success:
        print("\n🎉 RÉPARATION TERMINÉE !")
        print("Les anciennes images ont été supprimées.")
        print("Videz le cache de votre navigateur (Ctrl+F5) pour voir les changements.")
        print("\n💡 Si les images ne se rechargent pas correctement:")
        print("   • Videz le cache de votre navigateur")
        print("   • Re-synchronisez le produit depuis Shopify")
        print("   • Vérifiez que les nouvelles images ont les bonnes dimensions")
    else:
        print("\n❌ RÉPARATION ÉCHOUÉE")
        print("Vérifiez les logs ci-dessus pour plus de détails.")

if __name__ == "__main__":
    main()
