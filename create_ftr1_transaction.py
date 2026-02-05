#!/usr/bin/env python
"""
Script pour créer une transaction de test pour ftr1
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Post, Transaction, Chat, Message, Notification, Profile
from django.utils import timezone
import uuid

def create_ftr1_transaction():
    print('🎮 Création d\'une transaction de test pour ftr1')
    print('=' * 50)
    
    # Vérifier si ftr1 existe
    try:
        ftr1_user = User.objects.get(username='ftr1')
        print(f'✅ Utilisateur ftr1 trouvé: {ftr1_user.email}')
    except User.DoesNotExist:
        print('❌ Utilisateur ftr1 non trouvé')
        return
    
    # Créer un vendeur de test
    seller, created = User.objects.get_or_create(
        username='test_seller_ftr1',
        defaults={
            'email': 'seller@ftr1test.com',
            'first_name': 'Test',
            'last_name': 'Seller'
        }
    )
    if created:
        seller.set_password('testpass123')
        seller.save()
        Profile.objects.create(user=seller)
    
    print(f'✅ Vendeur: {seller.username}')
    
    # Créer un post de test
    post = Post.objects.create(
        title='Compte de test pour ftr1',
        user='test_seller_ftr1',
        author=seller,
        caption='Compte de test spécialement créé pour ftr1',
        price=75.00,
        email='test@ftr1.com',
        password='testpass123',
        game_type='FreeFire',
        coins='3000',
        level='75'
    )
    
    print(f'✅ Post créé: {post.title} - {post.price}€')
    
    # Créer la transaction
    transaction = Transaction.objects.create(
        buyer=ftr1_user,
        seller=seller,
        post=post,
        amount=75.00,
        status='processing'
    )
    
    print(f'✅ Transaction créée: {transaction.id}')
    print(f'✅ Statut: {transaction.get_status_display()}')
    
    # Créer le chat de transaction
    chat = Chat.objects.create(
        transaction=transaction,
        is_active=True,
        is_locked=False
    )
    
    print(f'✅ Chat créé: {chat.id}')
    
    # Créer quelques messages de test
    messages_data = [
        {'sender': ftr1_user, 'content': 'Bonjour, je suis intéressé par ce compte', 'type': 'text'},
        {'sender': seller, 'content': 'Salut ftr1 ! Oui, c\'est un excellent compte', 'type': 'text'},
        {'sender': ftr1_user, 'content': 'Parfait, je vais procéder au paiement', 'type': 'text'},
        {'sender': seller, 'content': 'D\'accord, je vous enverrai les informations après paiement', 'type': 'text'},
    ]
    
    for i, msg_data in enumerate(messages_data, 1):
        message = Message.objects.create(
            chat=chat,
            sender=msg_data['sender'],
            content=msg_data['content'],
            message_type=msg_data['type']
        )
        
        # Créer une notification pour l'autre utilisateur
        other_users = chat.get_other_users(msg_data['sender'])
        for other_user in other_users:
            Notification.objects.create(
                user=other_user,
                title='Nouveau message',
                content=f'Vous avez reçu un nouveau message de {msg_data["sender"].username}',
                type='new_message',
                message=message
            )
        
        print(f'✅ Message {i}: {message.content[:30]}...')
    
    print(f'\n🎉 Transaction de test créée avec succès pour ftr1 !')
    print(f'📊 Détails:')
    print(f'   - Transaction: {transaction.id}')
    print(f'   - Chat: {chat.id}')
    print(f'   - Messages: {Message.objects.filter(chat=chat).count()}')
    print(f'   - Notifications: {Notification.objects.filter(user=ftr1_user).count()}')
    print(f'\n💬 URL du chat: http://localhost:8000/chat/transaction/{transaction.id}/')
    print(f'🔗 URL de la liste des chats: http://localhost:8000/chat/list/')
    
    # Tester les méthodes du chat
    print(f'\n🔧 Test des méthodes du chat:')
    print(f'   - Accès ftr1: {chat.has_access(ftr1_user)}')
    print(f'   - Accès vendeur: {chat.has_access(seller)}')
    print(f'   - Autres utilisateurs (ftr1): {[u.username for u in chat.get_other_users(ftr1_user)]}')
    print(f'   - Autre utilisateur (ftr1): {chat.get_other_user(ftr1_user).username if chat.get_other_user(ftr1_user) else "None"}')

if __name__ == '__main__':
    create_ftr1_transaction()
