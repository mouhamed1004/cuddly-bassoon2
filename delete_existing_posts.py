#!/usr/bin/env python3
"""
Script pour supprimer toutes les annonces existantes
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, PostImage, PostVideo, Transaction

def delete_existing_posts():
    """Supprime toutes les annonces existantes"""
    print("🗑️ SUPPRESSION DES ANNONCES EXISTANTES")
    print("=" * 50)
    
    try:
        # Compter les annonces existantes
        total_posts = Post.objects.count()
        print(f"📊 Annonces existantes: {total_posts}")
        
        if total_posts == 0:
            print("✅ Aucune annonce à supprimer")
            return True
        
        # Supprimer les transactions liées
        transactions_count = Transaction.objects.filter(post__isnull=False).count()
        print(f"📊 Transactions liées: {transactions_count}")
        
        # Supprimer les images et vidéos
        images_count = PostImage.objects.count()
        videos_count = PostVideo.objects.count()
        print(f"📊 Images: {images_count}, Vidéos: {videos_count}")
        
        # Supprimer tout
        print("\n🗑️ Suppression en cours...")
        
        # Supprimer les transactions d'abord
        Transaction.objects.filter(post__isnull=False).delete()
        print("✅ Transactions supprimées")
        
        # Supprimer les images et vidéos
        PostImage.objects.all().delete()
        PostVideo.objects.all().delete()
        print("✅ Images et vidéos supprimées")
        
        # Supprimer les annonces
        Post.objects.all().delete()
        print("✅ Annonces supprimées")
        
        # Vérification
        remaining_posts = Post.objects.count()
        print(f"\n📊 Annonces restantes: {remaining_posts}")
        
        if remaining_posts == 0:
            print("🎉 Toutes les annonces ont été supprimées avec succès!")
            return True
        else:
            print("❌ Il reste des annonces à supprimer")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        return False

if __name__ == "__main__":
    delete_existing_posts()
