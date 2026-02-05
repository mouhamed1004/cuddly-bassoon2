#!/usr/bin/env python
"""
Script de test pour une transaction réelle avec chat
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Post, Transaction, Chat, Message, Notification, Profile, CinetPayTransaction
from django.utils import timezone
import uuid

def test_real_transaction_chat():
    print("🧪 Test d'une transaction réelle avec chat")
    print("=" * 50)
    
    # Récupérer ftr1
    try:
        ftr1_user = User.objects.get(username='ftr1')
        print(f'✅ Utilisateur ftr1 trouvé: {ftr1_user.email}')
    except User.DoesNotExist:
        print('❌ Utilisateur ftr1 non trouvé')
        return
    
    # Créer un vendeur de test
    seller, created = User.objects.get_or_create(
        username='test_seller_real_chat',
        defaults={
            'email': 'seller@realchat.com',
            'first_name': 'Test',
            'last_name': 'Real Chat'
        }
    )
    if created:
        seller.set_password('testpass123')
        seller.save()
        Profile.objects.create(user=seller)
    
    print(f'✅ Vendeur: {seller.username}')
    
    # Créer un post de test
    post = Post.objects.create(
        title='Compte de test chat réel',
        user='test_seller_real_chat',
        author=seller,
        caption='Compte de test pour le chat réel',
        price=75.00,
        email='test@realchat.com',
        password='testpass123',
        game_type='FreeFire',
        coins='3000',
        level='60'
    )
    
    print(f'✅ Post créé: {post.title} - {post.price}€')
    
    # Créer une transaction
    transaction = Transaction.objects.create(
        buyer=ftr1_user,
        seller=seller,
        post=post,
        amount=75.00,
        status='processing'
    )
    
    print(f'✅ Transaction créée: {transaction.id}')
    print(f'✅ Statut: {transaction.get_status_display()}')
    
    # Créer une transaction CinetPay simulée
    cinetpay_transaction = CinetPayTransaction.objects.create(
        transaction=transaction,
        cinetpay_transaction_id=str(uuid.uuid4()),
        status='payment_received',
        amount=75.00,
        currency='XOF',
        platform_commission=3.75,
        seller_amount=71.25
    )
    
    print(f'✅ Transaction CinetPay créée: {cinetpay_transaction.id}')
    print(f'✅ Statut CinetPay: {cinetpay_transaction.status}')
    
    # Tester la logique de la vue transaction_detail
    print(f'\n🔧 Test de la logique de la vue:')
    
    # Vérifier si le paiement CinetPay est validé
    cinetpay_payment_validated = False
    if hasattr(transaction, 'cinetpay_transaction'):
        cinetpay_payment_validated = transaction.cinetpay_transaction.status in ['payment_received', 'in_escrow', 'escrow_released', 'completed']
    
    print(f'   - Paiement CinetPay validé: {cinetpay_payment_validated}')
    
    # Vérifier s'il y a un litige ouvert
    has_open_dispute = False
    print(f'   - Litige ouvert: {has_open_dispute}')
    
    # Vérifier si le chat est activé
    chat_enabled = cinetpay_payment_validated and not has_open_dispute
    print(f'   - Chat activé: {chat_enabled}')
    
    # Tester la création du chat
    if chat_enabled:
        chat, created = Chat.objects.get_or_create(
            transaction=transaction,
            defaults={
                'is_active': True,
                'is_locked': False
            }
        )
        
        # Mettre à jour le statut de blocage selon le statut de la transaction
        chat.is_locked = transaction.status not in ['processing']
        chat.save()
        
        print(f'   - Chat créé: {chat.id}')
        print(f'   - Chat bloqué: {chat.is_locked}')
        print(f'   - Chat actif: {chat.is_active}')
        
        # Récupérer les messages
        messages = Message.objects.filter(chat=chat).order_by('created_at')
        print(f'   - Messages: {messages.count()}')
        
        # URL WebSocket
        websocket_url = f'ws://localhost:8000/ws/chat/transaction/{transaction.id}/'
        print(f'   - URL WebSocket: {websocket_url}')
        
        # Créer quelques messages de test
        print(f'\n📝 Création de messages de test...')
        
        messages_data = [
            {'sender': ftr1_user, 'content': 'Bonjour, j\'ai effectué le paiement. Pouvez-vous m\'envoyer les informations du compte ?', 'type': 'text'},
            {'sender': seller, 'content': 'Parfait ! Je vais vous envoyer les informations par message privé.', 'type': 'text'},
            {'sender': ftr1_user, 'content': 'Merci, j\'attends les informations.', 'type': 'text'},
            {'sender': seller, 'content': 'Voici les informations du compte : [Détails du compte]', 'type': 'text'},
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
            
            print(f'   ✅ Message {i}: {message.content[:30]}...')
    
    print(f'\n✅ Test terminé avec succès !')
    print(f'📊 Résumé:')
    print(f'   - Transaction: {transaction.id}')
    print(f'   - Statut: {transaction.get_status_display()}')
    print(f'   - Chat activé: {chat_enabled}')
    print(f'   - Chat bloqué: {chat.is_locked if chat_enabled else "N/A"}')
    print(f'   - Messages: {Message.objects.filter(chat=chat).count() if chat_enabled else 0}')
    print(f'   - Notifications: {Notification.objects.filter(user__in=[ftr1_user, seller]).count()}')
    
    print(f'\n💡 Instructions pour tester:')
    print(f'   1. Démarrer le serveur: python manage.py runserver')
    print(f'   2. Se connecter avec ftr1: http://localhost:8000/')
    print(f'   3. Aller sur: http://localhost:8000/transaction/{transaction.id}/')
    print(f'   4. Vérifier que le chat est intégré et fonctionnel')
    print(f'   5. Ouvrir la console du navigateur pour voir les logs de débogage')

if __name__ == '__main__':
    test_real_transaction_chat()
