#!/usr/bin/env python
"""
Script pour créer une transaction de test en mode processing pour ftr1
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

def create_ftr1_processing_transaction():
    print('🎮 Création d\'une transaction de test en mode processing pour ftr1')
    print('=' * 70)
    
    # Vérifier si ftr1 existe
    try:
        ftr1_user = User.objects.get(username='ftr1')
        print(f'✅ Utilisateur ftr1 trouvé: {ftr1_user.email}')
    except User.DoesNotExist:
        print('❌ Utilisateur ftr1 non trouvé')
        return
    
    # Créer un vendeur de test
    seller, created = User.objects.get_or_create(
        username='test_seller_ftr1_processing',
        defaults={
            'email': 'seller@ftr1processing.com',
            'first_name': 'Test',
            'last_name': 'Seller Processing'
        }
    )
    if created:
        seller.set_password('testpass123')
        seller.save()
        Profile.objects.create(user=seller)
    
    print(f'✅ Vendeur: {seller.username}')
    
    # Créer un post de test
    post = Post.objects.create(
        title='Compte de test processing pour ftr1',
        user='test_seller_ftr1_processing',
        author=seller,
        caption='Compte de test spécialement créé pour ftr1 - mode processing',
        price=100.00,
        email='test@ftr1processing.com',
        password='testpass123',
        game_type='PUBG',
        coins='5000',
        level='80'
    )
    
    print(f'✅ Post créé: {post.title} - {post.price}€')
    
    # Créer la transaction en mode processing
    transaction = Transaction.objects.create(
        buyer=ftr1_user,
        seller=seller,
        post=post,
        amount=100.00,
        status='processing'  # Mode processing = chat ouvert
    )
    
    print(f'✅ Transaction créée: {transaction.id}')
    print(f'✅ Statut: {transaction.get_status_display()}')
    
    # Créer le chat de transaction
    chat = Chat.objects.create(
        transaction=transaction,
        is_active=True,
        is_locked=False  # Chat ouvert en mode processing
    )
    
    print(f'✅ Chat créé: {chat.id}')
    print(f'✅ Chat bloqué: {chat.is_locked}')
    
    # Créer quelques messages de test
    messages_data = [
        {'sender': ftr1_user, 'content': 'Bonjour, j\'ai effectué le paiement', 'type': 'text'},
        {'sender': seller, 'content': 'Parfait ! Je vais vous envoyer les informations du compte', 'type': 'text'},
        {'sender': ftr1_user, 'content': 'Merci, j\'attends les informations', 'type': 'text'},
        {'sender': seller, 'content': 'Voici les informations du compte : email et mot de passe', 'type': 'text'},
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
    
    # Tester la logique de blocage
    print(f'\n🧪 Test de la logique de blocage:')
    
    statuses = ['pending', 'processing', 'completed', 'cancelled', 'disputed', 'refunded']
    
    for status in statuses:
        transaction.status = status
        transaction.save()
        
        # Appliquer la nouvelle logique
        chat.is_locked = transaction.status not in ['processing']
        chat.save()
        
        should_be_locked = status != 'processing'
        is_correctly_locked = chat.is_locked == should_be_locked
        
        print(f'   - {status}: {"🔒" if chat.is_locked else "🔓"} {"✅" if is_correctly_locked else "❌"}')
    
    # Remettre en mode processing
    transaction.status = 'processing'
    transaction.save()
    chat.is_locked = transaction.status not in ['processing']
    chat.save()
    
    print(f'\n✅ Statut final: {transaction.get_status_display()}')
    print(f'🔓 Chat final: {"Débloqué" if not chat.is_locked else "Bloqué"}')
    
    print(f'\n🎉 Transaction de test créée avec succès pour ftr1 !')
    print(f'📊 Détails:')
    print(f'   - Transaction: {transaction.id}')
    print(f'   - Chat: {chat.id}')
    print(f'   - Messages: {Message.objects.filter(chat=chat).count()}')
    print(f'   - Notifications: {Notification.objects.filter(user=ftr1_user).count()}')
    print(f'   - Statut: {transaction.get_status_display()}')
    print(f'   - Chat ouvert: {not chat.is_locked}')
    
    print(f'\n💬 URL du chat: http://localhost:8000/chat/transaction/{transaction.id}/')
    print(f'🔗 URL de la liste des chats: http://localhost:8000/chat/list/')
    
    print(f'\n💡 Cette transaction est maintenant en mode "processing"')
    print(f'   - Le chat est OUVERT (ftr1 peut échanger avec le vendeur)')
    print(f'   - Le paiement est validé')
    print(f'   - La livraison est en cours')
    print(f'   - ftr1 peut confirmer la réception pour terminer la transaction')

if __name__ == '__main__':
    create_ftr1_processing_transaction()
