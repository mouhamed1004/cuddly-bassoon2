#!/usr/bin/env python3
"""
Test avec une transaction réelle pour vérifier le chat.
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

def test_real_transaction():
    """Test avec une transaction réelle"""
    print("🧪 TEST AVEC TRANSACTION RÉELLE")
    print("=" * 50)
    
    # Créer des utilisateurs de test
    buyer, _ = User.objects.get_or_create(username='test_buyer_real', defaults={'password': 'test123'})
    seller, _ = User.objects.get_or_create(username='test_seller_real', defaults={'password': 'test123'})
    print("✅ Utilisateurs de test créés")
    
    # Créer une annonce de test
    post = Post.objects.create(
        title="Compte Test Réel",
        game_type="FIFA",
        level=50,
        coins=100000,
        price=25.00,
        user=buyer,
        email="test@example.com",
        password="testpass",
        caption="Compte pour test réel",
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
        customer_id="test_customer_real",
        customer_name="Test",
        customer_surname="User",
        customer_phone_number="+221123456789",
        customer_email="test@example.com",
        customer_address="Test Address",
        customer_city="Dakar",
        payment_token="test_token_real",
        status='payment_received',
        amount=transaction.amount,
        currency='XOF',
        platform_commission=2.50,
        seller_amount=transaction.amount - 2.50,
        cinetpay_transaction_id=f"test_cinetpay_real_{transaction.id}"
    )
    print(f"✅ Paiement CinetPay créé: {cinetpay.id}")
    
    # Test avec le client Django
    client = Client()
    client.force_login(buyer)
    
    # TEST 1: Accéder à la page de transaction
    print("\n📋 TEST 1: Page de transaction")
    print("-" * 30)
    
    response = client.get(f'/transaction/{transaction.id}/')
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCÈS: Page de transaction accessible")
    else:
        print(f"❌ ÉCHEC: Page de transaction inaccessible (status {response.status_code})")
        return False
    
    # TEST 2: Récupération des messages (doit être vide au début)
    print("\n📋 TEST 2: Récupération des messages (vide)")
    print("-" * 30)
    
    response = client.get(f'/transaction/{transaction.id}/messages/')
    print(f"   Status code: {response.status_code}")
    print(f"   Content-Type: {response.get('Content-Type', 'N/A')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"   Messages récupérés: {len(data.get('messages', []))}")
            print("✅ SUCCÈS: Récupération des messages fonctionne")
        except json.JSONDecodeError as e:
            print(f"❌ ÉCHEC: Réponse n'est pas du JSON valide: {e}")
            print(f"   Contenu: {response.content[:200]}...")
            return False
    else:
        print(f"❌ ÉCHEC: Status code {response.status_code}")
        print(f"   Contenu: {response.content[:200]}...")
        return False
    
    # TEST 3: Envoi du premier message
    print("\n📋 TEST 3: Envoi du premier message")
    print("-" * 30)
    
    response = client.post(f'/transaction/{transaction.id}/send-message/', {
        'content': 'Bonjour, j\'ai acheté votre compte'
    })
    print(f"   Status code: {response.status_code}")
    print(f"   Content-Type: {response.get('Content-Type', 'N/A')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message', {}).get('content', 'N/A')}")
            print("✅ SUCCÈS: Premier message envoyé")
        except json.JSONDecodeError as e:
            print(f"❌ ÉCHEC: Réponse n'est pas du JSON valide: {e}")
            print(f"   Contenu: {response.content[:200]}...")
            return False
    else:
        print(f"❌ ÉCHEC: Status code {response.status_code}")
        print(f"   Contenu: {response.content[:200]}...")
        return False
    
    # TEST 4: Vérifier que le message a été créé
    print("\n📋 TEST 4: Vérification du message créé")
    print("-" * 30)
    
    messages = Message.objects.filter(chat__transaction=transaction)
    print(f"   Messages en base: {messages.count()}")
    
    if messages.count() == 1:
        print("✅ SUCCÈS: Le message a été créé en base")
    else:
        print("❌ ÉCHEC: Le message n'a pas été créé")
        return False
    
    # TEST 5: Récupération des messages (maintenant avec 1 message)
    print("\n📋 TEST 5: Récupération des messages (avec 1 message)")
    print("-" * 30)
    
    response = client.get(f'/transaction/{transaction.id}/messages/')
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"   Messages récupérés: {len(data.get('messages', []))}")
            if len(data.get('messages', [])) == 1:
                print("✅ SUCCÈS: Le message est récupéré correctement")
            else:
                print("❌ ÉCHEC: Le message n'est pas récupéré")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ ÉCHEC: Réponse n'est pas du JSON valide: {e}")
            return False
    else:
        print(f"❌ ÉCHEC: Status code {response.status_code}")
        return False
    
    # TEST 6: Envoi d'un deuxième message
    print("\n📋 TEST 6: Envoi d'un deuxième message")
    print("-" * 30)
    
    response = client.post(f'/transaction/{transaction.id}/send-message/', {
        'content': 'Pouvez-vous me donner les identifiants ?'
    })
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print("✅ SUCCÈS: Deuxième message envoyé")
        except json.JSONDecodeError as e:
            print(f"❌ ÉCHEC: Réponse n'est pas du JSON valide: {e}")
            return False
    else:
        print(f"❌ ÉCHEC: Status code {response.status_code}")
        return False
    
    # TEST 7: Vérification finale
    print("\n📋 TEST 7: Vérification finale")
    print("-" * 30)
    
    messages = Message.objects.filter(chat__transaction=transaction)
    print(f"   Total messages en base: {messages.count()}")
    
    if messages.count() == 2:
        print("✅ SUCCÈS: Les deux messages sont en base")
    else:
        print("❌ ÉCHEC: Problème avec les messages")
        return False
    
    # Afficher les messages
    print("\n📋 Messages créés:")
    for i, msg in enumerate(messages, 1):
        print(f"   {i}. {msg.sender.username}: {msg.content}")
    
    # Nettoyage
    print("\n🧹 Nettoyage des données de test...")
    transaction.delete()
    post.delete()
    buyer.delete()
    seller.delete()
    print("✅ Nettoyage terminé")
    
    print("\n🎉 TOUS LES TESTS RÉELS ONT RÉUSSI!")
    print("=" * 50)
    print("✅ Page de transaction accessible")
    print("✅ Récupération des messages fonctionnelle")
    print("✅ Envoi de messages fonctionnel")
    print("✅ Messages stockés en base")
    print("✅ Pas d'erreur JSON/HTML")
    
    return True

if __name__ == '__main__':
    success = test_real_transaction()
    if success:
        print("\n✅ Test réussi !")
        sys.exit(0)
    else:
        print("\n❌ Test échoué !")
        sys.exit(1)
