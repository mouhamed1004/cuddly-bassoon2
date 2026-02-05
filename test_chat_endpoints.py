#!/usr/bin/env python3
"""
Test des endpoints du chat de transaction.
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from blizzgame.models import Post, Transaction, Chat, Message, CinetPayTransaction
import json

def test_chat_endpoints():
    """Test des endpoints du chat"""
    print("🧪 TEST DES ENDPOINTS DU CHAT")
    print("=" * 50)
    
    # Créer des utilisateurs de test
    buyer, _ = User.objects.get_or_create(username='test_buyer_endpoint', defaults={'password': 'test123'})
    seller, _ = User.objects.get_or_create(username='test_seller_endpoint', defaults={'password': 'test123'})
    print("✅ Utilisateurs de test créés")
    
    # Créer une annonce de test
    post = Post.objects.create(
        title="Compte Test Endpoint",
        game_type="FIFA",
        level=50,
        coins=100000,
        price=25.00,
        user=buyer,
        email="test@example.com",
        password="testpass",
        caption="Compte pour test des endpoints",
        author=seller,
        is_sold=False,
        is_on_sale=True
    )
    print(f"✅ Annonce créée: {post.title}")
    
    # Créer une transaction
    transaction = Transaction.objects.create(
        post=post,
        buyer=buyer,
        seller=seller,
        amount=post.price,
        status='processing'
    )
    print(f"✅ Transaction créée: {transaction.id}")
    
    # Créer un paiement CinetPay simulé
    cinetpay = CinetPayTransaction.objects.create(
        transaction=transaction,
        customer_id="test_customer_endpoint",
        customer_name="Test",
        customer_surname="User",
        customer_phone_number="+221123456789",
        customer_email="test@example.com",
        customer_address="Test Address",
        customer_city="Dakar",
        payment_token="test_token_endpoint",
        status='payment_received',
        amount=transaction.amount,
        currency='XOF',
        platform_commission=2.50,
        seller_amount=transaction.amount - 2.50,
        cinetpay_transaction_id=f"test_cinetpay_endpoint_{transaction.id}"
    )
    print(f"✅ Paiement CinetPay créé: {cinetpay.id}")
    
    # Créer un chat de transaction
    chat = Chat.objects.create(transaction=transaction)
    print(f"✅ Chat créé: {chat.id}")
    
    # Créer des messages de test
    message1 = Message.objects.create(
        chat=chat,
        sender=buyer,
        content="Message de test 1"
    )
    message2 = Message.objects.create(
        chat=chat,
        sender=seller,
        content="Message de test 2"
    )
    print(f"✅ Messages créés: {message1.id}, {message2.id}")
    
    # Test avec le client Django
    client = Client()
    client.force_login(buyer)
    
    # TEST 1: Récupération des messages
    print("\n📋 TEST 1: Récupération des messages")
    print("-" * 30)
    
    response = client.get(f'/transaction/{transaction.id}/messages/')
    print(f"   Status code: {response.status_code}")
    print(f"   Content-Type: {response.get('Content-Type', 'N/A')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"   Messages récupérés: {len(data.get('messages', []))}")
            print("✅ SUCCÈS: Endpoint de récupération fonctionne")
        except json.JSONDecodeError as e:
            print(f"❌ ÉCHEC: Réponse n'est pas du JSON valide: {e}")
            print(f"   Contenu: {response.content[:200]}...")
            return False
    else:
        print(f"❌ ÉCHEC: Status code {response.status_code}")
        print(f"   Contenu: {response.content[:200]}...")
        return False
    
    # TEST 2: Envoi de message
    print("\n📋 TEST 2: Envoi de message")
    print("-" * 30)
    
    response = client.post(f'/transaction/{transaction.id}/send-message/', {
        'content': 'Message de test via endpoint'
    })
    print(f"   Status code: {response.status_code}")
    print(f"   Content-Type: {response.get('Content-Type', 'N/A')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message', {}).get('content', 'N/A')}")
            print("✅ SUCCÈS: Endpoint d'envoi fonctionne")
        except json.JSONDecodeError as e:
            print(f"❌ ÉCHEC: Réponse n'est pas du JSON valide: {e}")
            print(f"   Contenu: {response.content[:200]}...")
            return False
    else:
        print(f"❌ ÉCHEC: Status code {response.status_code}")
        print(f"   Contenu: {response.content[:200]}...")
        return False
    
    # TEST 3: Vérifier que le message a été créé
    print("\n📋 TEST 3: Vérification du message créé")
    print("-" * 30)
    
    new_messages = Message.objects.filter(chat__transaction=transaction)
    print(f"   Total messages après envoi: {new_messages.count()}")
    
    if new_messages.count() == 3:
        print("✅ SUCCÈS: Le message a été créé en base")
    else:
        print("❌ ÉCHEC: Le message n'a pas été créé")
        return False
    
    # Nettoyage
    print("\n🧹 Nettoyage des données de test...")
    transaction.delete()
    post.delete()
    buyer.delete()
    seller.delete()
    print("✅ Nettoyage terminé")
    
    print("\n🎉 TOUS LES TESTS DES ENDPOINTS ONT RÉUSSI!")
    print("=" * 50)
    print("✅ Récupération des messages fonctionnelle")
    print("✅ Envoi de messages fonctionnel")
    print("✅ Réponses JSON valides")
    print("✅ Pas d'erreur HTML inattendue")
    
    return True

if __name__ == '__main__':
    success = test_chat_endpoints()
    if success:
        print("\n✅ Test réussi !")
        sys.exit(0)
    else:
        print("\n❌ Test échoué !")
        sys.exit(1)
