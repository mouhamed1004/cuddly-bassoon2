#!/usr/bin/env python
"""
Script pour supprimer TOUTES les notifications de chat
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Notification, Message, Chat

def remove_all_chat_notifications():
    """Supprime toutes les notifications liées aux chats"""
    print("🧹 Suppression de TOUTES les notifications de chat...")
    
    # Supprimer toutes les notifications de type 'new_message'
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
    
    # Supprimer aussi les notifications de litige si elles existent
    dispute_notifications = Notification.objects.filter(
        type='dispute_message'
    )
    
    dispute_count = dispute_notifications.count()
    if dispute_count > 0:
        dispute_notifications.delete()
        print(f"✅ {dispute_count} notifications de litige supprimées")
    
    # Vérifier les messages de chat
    chat_messages = Message.objects.all()
    print(f"📊 {chat_messages.count()} messages de chat dans la base de données")
    
    # Vérifier les chats
    chats = Chat.objects.all()
    print(f"📊 {chats.count()} chats dans la base de données")
    
    print("\n🎉 Nettoyage complet terminé !")
    print("💡 Toutes les notifications de chat ont été supprimées")

if __name__ == '__main__':
    remove_all_chat_notifications()

