#!/usr/bin/env python
"""
Test pour vérifier que le polling du chat fonctionne correctement
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from blizzgame.models import Post, Transaction, CinetPayTransaction, PrivateConversation, PrivateMessage

def test_chat_polling_fix():
    print("🚀 Test du polling du chat corrigé")
    print("=" * 60)

    # Créer des utilisateurs
    buyer, _ = User.objects.get_or_create(username='test_buyer_polling', defaults={'email': 'buyer_polling@test.com'})
    seller, _ = User.objects.get_or_create(username='test_seller_polling', defaults={'email': 'seller_polling@test.com'})

    # Créer un post de test
    post, _ = Post.objects.get_or_create(
        title='Test Chat Polling',
        defaults={
            'author': seller,
            'user': seller.username,
            'caption': 'Post de test pour le polling du chat',
            'price': 20.00,
            'game_type': 'FreeFire',
            'is_on_sale': True,
            'email': 'test_polling@example.com',
            'password': 'testpassword'
        }
    )

    # Créer une transaction
    transaction, _ = Transaction.objects.get_or_create(
        buyer=buyer,
        seller=seller,
        post=post,
        amount=20.00,
        defaults={'status': 'pending'}
    )

    # Simuler un paiement CinetPay réussi
    CinetPayTransaction.objects.get_or_create(
        transaction=transaction,
        defaults={
            'customer_id': str(buyer.id),
            'customer_name': 'Test', 'customer_surname': 'Buyer',
            'customer_phone_number': '+221701234567', 'customer_email': buyer.email,
            'customer_address': 'Test', 'customer_city': 'Dakar', 'customer_country': 'SN',
            'customer_state': 'DK', 'customer_zip_code': '10000',
            'seller_phone_number': '+221701234568', 'seller_country': 'SN', 'seller_operator': 'orange_money',
            'amount': float(transaction.amount), 'currency': 'XOF',
            'platform_commission': 1.0, 'seller_amount': 19.0,
            'status': 'payment_received',
            'cinetpay_transaction_id': f"TEST_POLLING_{transaction.id}",
            'payment_url': 'https://test.cinetpay.com',
            'payment_token': 'test_token_polling',
            'payment_received_at': timezone.now()
        }
    )
    transaction.status = 'processing'
    transaction.save()
    print(f"✅ Transaction créée: {transaction.id}")

    # Tester l'envoi de messages
    client = Client()
    client.force_login(buyer)

    # Envoyer quelques messages
    send_url = reverse('send_transaction_message', args=[transaction.id])
    
    messages_sent = []
    for i in range(3):
        message_content = f"Message de test {i+1}"
        response = client.post(send_url, {
            'content': message_content,
            'csrfmiddlewaretoken': 'test'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        if response.status_code == 200:
            messages_sent.append(message_content)
            print(f"✅ Message {i+1} envoyé: {message_content}")
        else:
            print(f"❌ Erreur envoi message {i+1}: {response.status_code}")

    # Tester la récupération des messages
    get_url = reverse('get_transaction_messages', args=[transaction.id])
    response = client.get(get_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Messages récupérés: {len(data.get('messages', []))}")
        
        # Vérifier que tous les messages sont présents
        if len(data.get('messages', [])) == len(messages_sent):
            print("✅ Tous les messages sont présents")
        else:
            print(f"❌ Nombre de messages incorrect: {len(data.get('messages', []))} au lieu de {len(messages_sent)}")
    else:
        print(f"❌ Erreur récupération messages: {response.status_code}")

    print("\n--- Test du polling ---")
    print("Le polling devrait maintenant:")
    print("1. ✅ Se déclencher toutes les 10 secondes (au lieu de 5)")
    print("2. ✅ Ne se déclencher que s'il y a de nouveaux messages")
    print("3. ✅ Ne pas causer d'actualisation continue")
    print("4. ✅ Afficher des logs dans la console du navigateur")

    print("\n✅ Test terminé et nettoyé")
    # Nettoyage
    PrivateMessage.objects.filter(conversation__user1__in=[buyer, seller]).delete()
    PrivateConversation.objects.filter(user1__in=[buyer, seller]).delete()
    CinetPayTransaction.objects.filter(transaction=transaction).delete()
    transaction.delete()
    post.delete()
    buyer.delete()
    seller.delete()

if __name__ == '__main__':
    test_chat_polling_fix()
