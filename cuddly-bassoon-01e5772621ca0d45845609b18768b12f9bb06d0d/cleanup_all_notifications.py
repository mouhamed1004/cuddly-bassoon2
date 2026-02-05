#!/usr/bin/env python
"""
Script pour nettoyer TOUTES les notifications et messages Django
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Notification, Message, Chat
from django.contrib import messages

def cleanup_all_notifications():
    """Supprime toutes les notifications et nettoie le système de messages"""
    print("🧹 Nettoyage complet de toutes les notifications...")
    
    # Supprimer toutes les notifications
    notifications_count = Notification.objects.count()
    Notification.objects.all().delete()
    print(f"✅ {notifications_count} notifications supprimées")
    
    # Vérifier les messages de chat
    chat_messages = Message.objects.all()
    print(f"📊 {chat_messages.count()} messages de chat dans la base de données")
    
    # Vérifier les chats
    chats = Chat.objects.all()
    print(f"📊 {chats.count()} chats dans la base de données")
    
    print("\n🎉 Nettoyage complet terminé !")
    print("💡 Toutes les notifications ont été supprimées")
    print("💡 Le système de messages Django ne devrait plus afficher de notifications parasites")

if __name__ == '__main__':
    cleanup_all_notifications()
