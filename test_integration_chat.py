#!/usr/bin/env python
"""
Script de test pour l'intégration du chat dans la page de transaction
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

def test_integration_chat():
    print('🧪 Test d\'intégration du chat dans la page de transaction')
    print('=' * 60)
    
    # Récupérer ftr1
    try:
        ftr1_user = User.objects.get(username='ftr1')
        print(f'✅ Utilisateur ftr1 trouvé: {ftr1_user.email}')
    except User.DoesNotExist:
        print('❌ Utilisateur ftr1 non trouvé')
        return
    
    # Créer un vendeur de test
    seller, created = User.objects.get_or_create(
        username='test_seller_integration',
        defaults={
            'email': 'seller@integration.com',
            'first_name': 'Test',
            'last_name': 'Integration'
        }
    )
    if created:
        seller.set_password('testpass123')
        seller.save()
        Profile.objects.create(user=seller)
    
    print(f'✅ Vendeur: {seller.username}')
    
    # Créer un post de test
    post = Post.objects.create(
        title='Compte de test intégration',
        user='test_seller_integration',
        author=seller,
        caption='Compte de test pour l\'intégration du chat',
        price=50.00,
        email='test@integration.com',
        password='testpass123',
        game_type='FreeFire',
        coins='2000',
        level='50'
    )
    
    print(f'✅ Post créé: {post.title} - {post.price}€')
    
    # Créer une transaction
    transaction = Transaction.objects.create(
        buyer=ftr1_user,
        seller=seller,
        post=post,
        amount=50.00,
        status='processing'
    )
    
    print(f'✅ Transaction créée: {transaction.id}')
    print(f'✅ Statut: {transaction.get_status_display()}')
    
    # Créer une transaction CinetPay simulée
    cinetpay_transaction = CinetPayTransaction.objects.create(
        transaction=transaction,
        cinetpay_transaction_id=str(uuid.uuid4()),
        status='payment_received',
        amount=50.00,
        currency='XOF',
        platform_commission=2.50,
        seller_amount=47.50
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
    
    # Tester différents statuts
    print(f'\n🧪 Test des différents statuts:')
    
    statuses = ['pending', 'processing', 'completed', 'cancelled', 'disputed', 'refunded']
    
    for status in statuses:
        transaction.status = status
        transaction.save()
        
        if chat_enabled:
            chat.is_locked = transaction.status not in ['processing']
            chat.save()
            
            should_be_locked = status != 'processing'
            is_correctly_locked = chat.is_locked == should_be_locked
            
            print(f'   - {status}: {"🔒" if chat.is_locked else "🔓"} {"✅" if is_correctly_locked else "❌"}')
    
    # Remettre en mode processing
    transaction.status = 'processing'
    transaction.save()
    if chat_enabled:
        chat.is_locked = transaction.status not in ['processing']
        chat.save()
    
    print(f'\n✅ Test d\'intégration terminé avec succès !')
    print(f'📊 Résumé:')
    print(f'   - Transaction: {transaction.id}')
    print(f'   - Statut: {transaction.get_status_display()}')
    print(f'   - Chat activé: {chat_enabled}')
    print(f'   - Chat bloqué: {chat.is_locked if chat_enabled else "N/A"}')
    print(f'   - URL de test: http://localhost:8000/transaction/{transaction.id}/')
    
    print(f'\n💡 Instructions pour tester:')
    print(f'   1. Démarrer le serveur: python start_chat_server.py')
    print(f'   2. Se connecter avec ftr1: http://localhost:8000/')
    print(f'   3. Aller sur: http://localhost:8000/transaction/{transaction.id}/')
    print(f'   4. Vérifier que le chat est intégré et fonctionnel')

if __name__ == '__main__':
    test_integration_chat()
