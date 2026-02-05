#!/usr/bin/env python
'''
Script de nettoyage des données de test du système de chat
'''
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Post, Transaction, Chat, Message, Dispute, Notification

def cleanup_test_data():
    print("🧹 Nettoyage des données de test du système de chat")
    print("=" * 50)
    
    # Supprimer les utilisateurs de test
    test_users = ['test_buyer_chat', 'test_seller_chat', 'test_admin_chat']
    for username in test_users:
        try:
            user = User.objects.get(username=username)
            user.delete()
            print(f"✅ Utilisateur supprimé: {username}")
        except User.DoesNotExist:
            print(f"⚠️ Utilisateur non trouvé: {username}")
    
    # Supprimer les posts de test
    test_posts = Post.objects.filter(title__contains='test pour chat')
    count = test_posts.count()
    test_posts.delete()
    print(f"✅ {count} posts de test supprimés")
    
    # Supprimer les transactions de test
    test_transactions = Transaction.objects.filter(
        buyer__username__in=test_users,
        seller__username__in=test_users
    )
    count = test_transactions.count()
    test_transactions.delete()
    print(f"✅ {count} transactions de test supprimées")
    
    # Supprimer les chats de test
    test_chats = Chat.objects.filter(
        transaction__buyer__username__in=test_users,
        transaction__seller__username__in=test_users
    )
    count = test_chats.count()
    test_chats.delete()
    print(f"✅ {count} chats de test supprimés")
    
    # Supprimer les messages de test
    test_messages = Message.objects.filter(
        sender__username__in=test_users
    )
    count = test_messages.count()
    test_messages.delete()
    print(f"✅ {count} messages de test supprimés")
    
    # Supprimer les litiges de test
    test_disputes = Dispute.objects.filter(
        opened_by__username__in=test_users
    )
    count = test_disputes.count()
    test_disputes.delete()
    print(f"✅ {count} litiges de test supprimés")
    
    # Supprimer les notifications de test
    test_notifications = Notification.objects.filter(
        user__username__in=test_users
    )
    count = test_notifications.count()
    test_notifications.delete()
    print(f"✅ {count} notifications de test supprimées")
    
    print("\n🎉 Nettoyage terminé avec succès !")

if __name__ == '__main__':
    cleanup_test_data()
