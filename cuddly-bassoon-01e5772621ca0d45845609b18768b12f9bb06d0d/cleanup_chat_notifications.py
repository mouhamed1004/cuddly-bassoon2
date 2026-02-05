#!/usr/bin/env python
"""
Script pour nettoyer les notifications de chat qui causent des problèmes
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Notification, Message, Chat

def cleanup_chat_notifications():
    """Nettoie les notifications de chat problématiques"""
    print("🧹 Nettoyage des notifications de chat...")
    
    # Supprimer les notifications de type 'new_message' liées aux chats
    notifications_to_delete = Notification.objects.filter(
        type='new_message'
    )
    
    count = notifications_to_delete.count()
    print(f"📊 {count} notifications de chat trouvées")
    
    if count > 0:
        notifications_to_delete.delete()
        print(f"✅ {count} notifications de chat supprimées")
    else:
        print("✅ Aucune notification de chat à supprimer")
    
    # Vérifier les messages de chat
    chat_messages = Message.objects.all()
    print(f"📊 {chat_messages.count()} messages de chat dans la base de données")
    
    # Vérifier les chats
    chats = Chat.objects.all()
    print(f"📊 {chats.count()} chats dans la base de données")
    
    print("\n🎉 Nettoyage terminé !")
    print("💡 Les notifications de chat ne s'afficheront plus à chaque actualisation")

if __name__ == '__main__':
    cleanup_chat_notifications()

