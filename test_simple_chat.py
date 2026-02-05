#!/usr/bin/env python
"""
Script de test simple pour le chat
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Transaction, Chat, Message, Notification

def test_simple_chat():
    print("🧪 Test simple du chat")
    print("=" * 40)
    
    # Récupérer la transaction de test
    transaction = Transaction.objects.filter(status='processing').first()
    if not transaction:
        print("❌ Aucune transaction en mode processing trouvée")
        return
    
    print(f"✅ Transaction: {transaction.id}")
    print(f"✅ Statut: {transaction.get_status_display()}")
    print(f"✅ Acheteur: {transaction.buyer.username}")
    print(f"✅ Vendeur: {transaction.seller.username}")
    
    # Récupérer ou créer le chat
    chat, created = Chat.objects.get_or_create(
        transaction=transaction,
        defaults={
            'is_active': True,
            'is_locked': False
        }
    )
    
    print(f"✅ Chat: {chat.id}")
    print(f"✅ Chat actif: {chat.is_active}")
    print(f"✅ Chat bloqué: {chat.is_locked}")
    
    # Vérifier les messages existants
    messages = Message.objects.filter(chat=chat)
    print(f"✅ Messages existants: {messages.count()}")
    
    for message in messages:
        print(f"   - {message.sender.username}: {message.content}")
    
    # Tester la création d'un nouveau message
    print(f"\n📝 Test de création d'un nouveau message...")
    
    try:
        new_message = Message.objects.create(
            chat=chat,
            sender=transaction.buyer,
            content="Nouveau message de test",
            message_type='text'
        )
        
        print(f"✅ Message créé: {new_message.id}")
        print(f"✅ Contenu: {new_message.content}")
        print(f"✅ Expéditeur: {new_message.sender.username}")
        print(f"✅ Type: {new_message.message_type}")
        print(f"✅ Créé: {new_message.created_at}")
        
        # Vérifier les autres utilisateurs
        other_users = chat.get_other_users(transaction.buyer)
        print(f"✅ Autres utilisateurs: {[u.username for u in other_users]}")
        
        # Créer des notifications
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
                    
            except Exception as e:
        print(f"❌ Erreur lors de la création du message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_simple_chat()
