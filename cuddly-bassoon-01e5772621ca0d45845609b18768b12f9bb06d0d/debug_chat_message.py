#!/usr/bin/env python
"""
Script de débogage pour le chat
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Transaction, Chat, Message, Notification

def debug_chat_message():
    print("🔍 Débogage du système de chat")
    print("=" * 50)
    
    # Récupérer une transaction de test
    try:
        transaction = Transaction.objects.filter(status='processing').first()
        if not transaction:
            print("❌ Aucune transaction en mode processing trouvée")
            return
        
        print(f"✅ Transaction trouvée: {transaction.id}")
        print(f"✅ Statut: {transaction.get_status_display()}")
        print(f"✅ Acheteur: {transaction.buyer.username}")
        print(f"✅ Vendeur: {transaction.seller.username}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # Vérifier le chat
    try:
        chat = Chat.objects.get(transaction=transaction)
        print(f"✅ Chat trouvé: {chat.id}")
        print(f"✅ Chat actif: {chat.is_active}")
        print(f"✅ Chat bloqué: {chat.is_locked}")
    except Chat.DoesNotExist:
        print("❌ Chat non trouvé")
        return
    
    # Vérifier les messages existants
    messages = Message.objects.filter(chat=chat)
    print(f"✅ Messages existants: {messages.count()}")
    
    for message in messages:
        print(f"   - {message.sender.username}: {message.content[:30]}...")
    
    # Tester la création d'un message
    print(f"\n🧪 Test de création d'un message...")
    
    try:
        # Créer un message de test
        test_message = Message.objects.create(
            chat=chat,
            sender=transaction.buyer,
            content="Message de test pour débogage",
            message_type='text'
        )
        
        print(f"✅ Message créé: {test_message.id}")
        print(f"✅ Contenu: {test_message.content}")
        print(f"✅ Expéditeur: {test_message.sender.username}")
        print(f"✅ Type: {test_message.message_type}")
        print(f"✅ Créé: {test_message.created_at}")
        
        # Tester la création de notification
        other_users = chat.get_other_users(transaction.buyer)
        print(f"✅ Autres utilisateurs: {[u.username for u in other_users]}")
        
        for other_user in other_users:
            notification = Notification.objects.create(
                user=other_user,
                title='Nouveau message',
                content=f'Vous avez reçu un nouveau message de {transaction.buyer.username}',
                type='new_message',
                message=test_message
            )
            print(f"✅ Notification créée: {notification.id}")
        
        # Vérifier les notifications
        notifications = Notification.objects.filter(user__in=other_users)
        print(f"✅ Notifications créées: {notifications.count()}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du message: {e}")
        import traceback
        traceback.print_exc()
    
    # Vérifier la logique de blocage
    print(f"\n🔒 Test de la logique de blocage...")
    
    statuses = ['pending', 'processing', 'completed', 'cancelled', 'disputed', 'refunded']
    
    for status in statuses:
        transaction.status = status
        transaction.save()
        
        chat.is_locked = transaction.status not in ['processing']
        chat.save()
        
        should_be_locked = status != 'processing'
        is_correctly_locked = chat.is_locked == should_be_locked
        
        print(f"   - {status}: {'🔒' if chat.is_locked else '🔓'} {'✅' if is_correctly_locked else '❌'}")
    
    # Remettre en mode processing
    transaction.status = 'processing'
    transaction.save()
    chat.is_locked = transaction.status not in ['processing']
    chat.save()
    
    print(f"\n✅ Débogage terminé !")
    print(f"📊 Résumé:")
    print(f"   - Transaction: {transaction.id}")
    print(f"   - Chat: {chat.id}")
    print(f"   - Messages: {Message.objects.filter(chat=chat).count()}")
    print(f"   - Notifications: {Notification.objects.filter(user__in=[transaction.buyer, transaction.seller]).count()}")
    print(f"   - Statut: {transaction.get_status_display()}")
    print(f"   - Chat bloqué: {chat.is_locked}")

if __name__ == '__main__':
    debug_chat_message()
