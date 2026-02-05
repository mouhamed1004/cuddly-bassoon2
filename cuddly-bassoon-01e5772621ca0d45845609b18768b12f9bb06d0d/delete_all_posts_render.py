#!/usr/bin/env python3
"""
Script pour supprimer TOUTES les annonces sur RENDER (PRODUCTION)
ATTENTION: Ce script supprime les donnees de PRODUCTION!
"""
import os
import sys
import django

# Configuration Django pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, PostImage, Transaction, Chat, Message, Notification
from django.contrib.auth.models import User

def delete_all_posts_render():
    """Supprime TOUTES les annonces sur RENDER (PRODUCTION)"""
    print("=" * 80)
    print("ATTENTION: SUPPRESSION SUR RENDER (PRODUCTION)")
    print("=" * 80)
    print("Ce script va supprimer TOUTES les annonces de la base de donnees")
    print("de production sur Render. Cette action est IRREVERSIBLE!")
    print("=" * 80)
    
    try:
        # Compter les elements existants
        total_posts = Post.objects.count()
        total_images = PostImage.objects.count()
        total_transactions = Transaction.objects.count()
        total_chats = Chat.objects.count()
        total_messages = Message.objects.count()
        total_notifications = Notification.objects.count()
        
        print(f"\nELEMENTS A SUPPRIMER SUR RENDER :")
        print(f"   - Annonces (Post): {total_posts}")
        print(f"   - Images (PostImage): {total_images}")
        print(f"   - Transactions: {total_transactions}")
        print(f"   - Chats: {total_chats}")
        print(f"   - Messages: {total_messages}")
        print(f"   - Notifications: {total_notifications}")
        
        if total_posts == 0:
            print("\nAucune annonce a supprimer sur Render")
            return True
        
        # Confirmation finale
        print(f"\n" + "!" * 60)
        print("DERNIERE CHANCE!")
        print("Vous etes sur le point de supprimer {total_posts} annonces")
        print("de la base de donnees de PRODUCTION sur Render!")
        print("Cette action est DEFINITIVEMENT IRREVERSIBLE!")
        print("!" * 60)
        
        # Supprimer dans l'ordre correct (dependances)
        print("\nSuppression en cours sur Render...")
        
        # 1. Supprimer les messages de chat
        Message.objects.all().delete()
        print("Messages supprimes")
        
        # 2. Supprimer les chats
        Chat.objects.all().delete()
        print("Chats supprimes")
        
        # 3. Supprimer les notifications
        Notification.objects.all().delete()
        print("Notifications supprimees")
        
        # 4. Supprimer les transactions
        Transaction.objects.all().delete()
        print("Transactions supprimees")
        
        # 5. Supprimer les images
        PostImage.objects.all().delete()
        print("Images supprimees")
        
        # 6. Supprimer les annonces
        Post.objects.all().delete()
        print("Annonces supprimees")
        
        # Verification finale
        remaining_posts = Post.objects.count()
        remaining_images = PostImage.objects.count()
        remaining_transactions = Transaction.objects.count()
        remaining_chats = Chat.objects.count()
        remaining_messages = Message.objects.count()
        remaining_notifications = Notification.objects.count()
        
        print(f"\nVERIFICATION FINALE SUR RENDER :")
        print(f"   - Annonces restantes: {remaining_posts}")
        print(f"   - Images restantes: {remaining_images}")
        print(f"   - Transactions restantes: {remaining_transactions}")
        print(f"   - Chats restants: {remaining_chats}")
        print(f"   - Messages restants: {remaining_messages}")
        print(f"   - Notifications restantes: {remaining_notifications}")
        
        if (remaining_posts == 0 and remaining_images == 0 and 
            remaining_transactions == 0 and remaining_chats == 0 and 
            remaining_messages == 0 and remaining_notifications == 0):
            print("\n" + "=" * 60)
            print("SUPPRESSION COMPLETE REUSSIE SUR RENDER!")
            print("Toutes les annonces de production ont ete supprimees.")
            print("=" * 60)
            return True
        else:
            print("\nERREUR: Certains elements n'ont pas ete supprimes sur Render")
            return False
            
    except Exception as e:
        print(f"\nERREUR lors de la suppression sur Render: {e}")
        return False

if __name__ == "__main__":
    print("Demarrage de la suppression sur RENDER (PRODUCTION)...")
    print("ATTENTION: Ceci va affecter la base de donnees de production!")
    
    # Double confirmation
    print("\nVoulez-vous vraiment continuer? (oui/non)")
    response = input().lower().strip()
    
    if response in ['oui', 'o', 'yes', 'y']:
        success = delete_all_posts_render()
        
        if success:
            print("\nScript termine avec succes sur Render")
            sys.exit(0)
        else:
            print("\nScript termine avec des erreurs sur Render")
            sys.exit(1)
    else:
        print("Suppression annulee par l'utilisateur")
        sys.exit(0)

