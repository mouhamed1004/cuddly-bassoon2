#!/usr/bin/env python3
"""
Script simple pour supprimer toutes les annonces sur Render
A exécuter directement dans la console Render
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, PostImage, Transaction, Chat, Message, Notification

def delete_all():
    print("=== SUPPRESSION DES ANNONCES SUR RENDER ===")
    
    # Compter avant suppression
    posts_count = Post.objects.count()
    images_count = PostImage.objects.count()
    transactions_count = Transaction.objects.count()
    chats_count = Chat.objects.count()
    messages_count = Message.objects.count()
    notifications_count = Notification.objects.count()
    
    print(f"Annonces: {posts_count}")
    print(f"Images: {images_count}")
    print(f"Transactions: {transactions_count}")
    print(f"Chats: {chats_count}")
    print(f"Messages: {messages_count}")
    print(f"Notifications: {notifications_count}")
    
    if posts_count == 0:
        print("Aucune annonce a supprimer")
        return
    
    print("\nSuppression en cours...")
    
    # Supprimer dans l'ordre
    Message.objects.all().delete()
    print("Messages supprimes")
    
    Chat.objects.all().delete()
    print("Chats supprimes")
    
    Notification.objects.all().delete()
    print("Notifications supprimees")
    
    Transaction.objects.all().delete()
    print("Transactions supprimees")
    
    PostImage.objects.all().delete()
    print("Images supprimees")
    
    Post.objects.all().delete()
    print("Annonces supprimees")
    
    # Verification
    remaining_posts = Post.objects.count()
    print(f"\nAnnonces restantes: {remaining_posts}")
    
    if remaining_posts == 0:
        print("SUPPRESSION REUSSIE!")
    else:
        print("ERREUR: Des annonces restent")

# Exécuter directement
delete_all()

