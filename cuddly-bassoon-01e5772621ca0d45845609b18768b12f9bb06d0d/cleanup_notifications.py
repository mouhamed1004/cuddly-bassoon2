#!/usr/bin/env python
"""
Script pour nettoyer les notifications inutiles
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Notification

def cleanup_notifications():
    print("🧹 Nettoyage des notifications inutiles")
    print("=" * 50)
    
    # Supprimer les notifications de type 'private_message' qui ne sont pas utiles
    private_message_notifications = Notification.objects.filter(type='private_message')
    count = private_message_notifications.count()
    
    if count > 0:
        print(f"📧 Notifications de messages privés trouvées: {count}")
        
        # Afficher quelques exemples
        for notification in private_message_notifications[:5]:
            print(f"   - {notification.title}: {notification.content[:50]}...")
        
        # Supprimer
        private_message_notifications.delete()
        print(f"✅ {count} notifications supprimées")
    else:
        print("✅ Aucune notification de message privé trouvée")
    
    # Supprimer les notifications vides ou inutiles
    empty_notifications = Notification.objects.filter(
        content__in=['', 'Private message from', 'Message from']
    )
    empty_count = empty_notifications.count()
    
    if empty_count > 0:
        print(f"📭 Notifications vides trouvées: {empty_count}")
        empty_notifications.delete()
        print(f"✅ {empty_count} notifications vides supprimées")
    
    # Afficher le résumé
    total_notifications = Notification.objects.count()
    print(f"\n📊 Total des notifications restantes: {total_notifications}")
    
    print("\n✅ Nettoyage terminé!")

if __name__ == '__main__':
    cleanup_notifications()
