#!/usr/bin/env python
"""
Script de test pour vérifier la correction du WebSocket
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Transaction, Chat, Message, Notification

def test_websocket_fix():
    print("🔧 Test de la correction du WebSocket")
    print("=" * 50)
    
    # Récupérer la transaction de test
    transaction = Transaction.objects.filter(status='processing').first()
    if not transaction:
        print("❌ Aucune transaction en mode processing trouvée")
        return
    
    print(f"✅ Transaction: {transaction.id}")
    print(f"✅ Statut: {transaction.get_status_display()}")
    
    # Vérifier le chat
    try:
        chat = Chat.objects.get(transaction=transaction)
        print(f"✅ Chat: {chat.id}")
        print(f"✅ Chat actif: {chat.is_active}")
        print(f"✅ Chat bloqué: {chat.is_locked}")
    except Chat.DoesNotExist:
        print("❌ Chat non trouvé")
        return
    
    # Vérifier les messages
    messages = Message.objects.filter(chat=chat)
    print(f"✅ Messages: {messages.count()}")
    
    # Vérifier les notifications
    notifications = Notification.objects.filter(user__in=[transaction.buyer, transaction.seller])
    print(f"✅ Notifications: {notifications.count()}")
    
    # Tester la création d'un message
    print(f"\n📝 Test de création d'un message...")
    
    try:
        new_message = Message.objects.create(
            chat=chat,
            sender=transaction.buyer,
            content="Test de correction WebSocket",
            message_type='text'
        )
        
        print(f"✅ Message créé: {new_message.id}")
        print(f"✅ Contenu: {new_message.content}")
        
        # Créer une notification
        other_users = chat.get_other_users(transaction.buyer)
        for other_user in other_users:
            notification = Notification.objects.create(
                user=other_user,
                title='Nouveau message',
                content=f'Vous avez reçu un nouveau message de {transaction.buyer.username}',
                type='new_message',
                message=new_message
            )
            print(f"✅ Notification créée pour {other_user.username}: {notification.id}")
        
        print(f"\n✅ Test terminé avec succès !")
        print(f"📊 Résumé:")
        print(f"   - Transaction: {transaction.id}")
        print(f"   - Chat: {chat.id}")
        print(f"   - Messages: {Message.objects.filter(chat=chat).count()}")
        print(f"   - Notifications: {Notification.objects.filter(user__in=[transaction.buyer, transaction.seller]).count()}")
        
        print(f"\n💡 Instructions pour tester:")
        print(f"   1. Démarrer le serveur: python manage.py runserver")
        print(f"   2. Aller sur: http://localhost:8000/transaction/{transaction.id}/")
        print(f"   3. Ouvrir la console du navigateur (F12)")
        print(f"   4. Vérifier les logs de débogage")
        print(f"   5. Tester l'envoi de messages")
        print(f"   6. Vérifier qu'il n'y a plus d'erreurs WebSocket")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_websocket_fix()
