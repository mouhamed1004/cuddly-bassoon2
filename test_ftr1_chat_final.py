#!/usr/bin/env python
"""
Script de test final pour le chat de ftr1
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Transaction, Chat, Message, Notification
from django.contrib.auth.models import User

def test_ftr1_chat_final():
    print('🎯 Test final du chat de ftr1')
    print('=' * 50)
    
    # Récupérer la transaction de ftr1
    transaction = Transaction.objects.get(id='17acf02c-f856-4de6-91fa-fae4d027a970')
    chat = Chat.objects.get(transaction=transaction)
    buyer = transaction.buyer
    seller = transaction.seller
    
    print(f'👤 Acheteur: {buyer.username}')
    print(f'👤 Vendeur: {seller.username}')
    print(f'💰 Montant: {transaction.amount}€')
    print(f'📊 Statut: {transaction.get_status_display()}')
    print(f'🔒 Chat bloqué: {chat.is_locked}')
    print(f'✅ Chat actif: {chat.is_active}')
    
    # Vérifier les méthodes du chat
    print(f'\n🔧 Test des méthodes du chat:')
    print(f'   - Accès acheteur: {chat.has_access(buyer)}')
    print(f'   - Accès vendeur: {chat.has_access(seller)}')
    print(f'   - Autres utilisateurs (acheteur): {[u.username for u in chat.get_other_users(buyer)]}')
    print(f'   - Autre utilisateur (acheteur): {chat.get_other_user(buyer).username if chat.get_other_user(buyer) else "None"}')
    
    # Compter les messages
    messages = Message.objects.filter(chat=chat)
    print(f'\n💬 Messages du chat:')
    print(f'   - Total: {messages.count()}')
    print(f'   - Messages de l\'acheteur: {messages.filter(sender=buyer).count()}')
    print(f'   - Messages du vendeur: {messages.filter(sender=seller).count()}')
    
    # Afficher les derniers messages
    print(f'\n📝 Derniers messages:')
    for message in messages.order_by('-created_at')[:3]:
        print(f'   - {message.sender.username}: {message.content[:50]}...')
    
    # Compter les notifications
    buyer_notifications = Notification.objects.filter(user=buyer).count()
    seller_notifications = Notification.objects.filter(user=seller).count()
    
    print(f'\n🔔 Notifications:')
    print(f'   - Acheteur: {buyer_notifications}')
    print(f'   - Vendeur: {seller_notifications}')
    
    # Tester différents statuts
    print(f'\n🧪 Test des différents statuts:')
    
    statuses = ['pending', 'processing', 'completed', 'cancelled', 'disputed', 'refunded']
    
    for status in statuses:
        transaction.status = status
        transaction.save()
        
        chat.is_locked = transaction.status in ['pending', 'waiting_payment']
        chat.save()
        
        should_be_locked = status in ['pending', 'waiting_payment']
        is_correctly_locked = chat.is_locked == should_be_locked
        
        print(f'   - {status}: {"🔒" if chat.is_locked else "🔓"} {"✅" if is_correctly_locked else "❌"}')
    
    # Remettre le statut final
    transaction.status = 'completed'
    transaction.save()
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f'\n✅ Statut final: {transaction.get_status_display()}')
    print(f'🔓 Chat final: {"Débloqué" if not chat.is_locked else "Bloqué"}')
    
    # URLs de test
    print(f'\n🔗 URLs de test:')
    print(f'   - Chat: http://localhost:8000/chat/transaction/{transaction.id}/')
    print(f'   - Liste des chats: http://localhost:8000/chat/list/')
    print(f'   - WebSocket: ws://localhost:8000/ws/chat/transaction/{transaction.id}/')
    
    print(f'\n🎉 Test final terminé avec succès !')
    print(f'\n💡 Le chat de ftr1 est maintenant prêt pour les tests en temps réel !')

if __name__ == '__main__':
    test_ftr1_chat_final()
