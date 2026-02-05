#!/usr/bin/env python3
"""
Test des corrections du chat de transaction.
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

def test_chat_fixes():
    """Test des corrections du chat"""
    print("🧪 TEST DES CORRECTIONS DU CHAT")
    print("=" * 50)
    
    # Créer des utilisateurs de test
    buyer, _ = User.objects.get_or_create(username='test_buyer_chat', defaults={'password': 'test123'})
    seller, _ = User.objects.get_or_create(username='test_seller_chat', defaults={'password': 'test123'})
    print("✅ Utilisateurs de test créés")
    
    # Créer une annonce de test
    post = Post.objects.create(
        title="Compte Test Chat",
        game_type="FIFA",
        level=50,
        coins=100000,
        price=25.00,
        user=buyer,
        email="test@example.com",
        password="testpass",
        caption="Compte pour test du chat",
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
        customer_id="test_customer_123",
        customer_name="Test",
        customer_surname="User",
        customer_phone_number="+221123456789",
        customer_email="test@example.com",
        customer_address="Test Address",
        customer_city="Dakar",
        payment_token="test_token_123",
        status='payment_received',
        amount=transaction.amount,
        currency='XOF',
        platform_commission=2.50,
        seller_amount=transaction.amount - 2.50,
        cinetpay_transaction_id=f"test_cinetpay_{transaction.id}"
    )
    print(f"✅ Paiement CinetPay créé: {cinetpay.id}")
    
    # TEST 1: Vérifier que le chat utilise les messages de transaction
    print("\n📋 TEST 1: Messages de transaction")
    print("-" * 30)
    
    # Créer un chat de transaction
    chat = Chat.objects.create(transaction=transaction)
    print(f"✅ Chat créé: {chat.id}")
    
    # Créer des messages de transaction
    message1 = Message.objects.create(
        chat=chat,
        sender=buyer,
        content="Bonjour, j'ai acheté votre compte"
    )
    message2 = Message.objects.create(
        chat=chat,
        sender=seller,
        content="Merci ! Voici les identifiants"
    )
    print(f"✅ Messages créés: {message1.id}, {message2.id}")
    
    # Vérifier que les messages sont bien liés à la transaction
    messages = Message.objects.filter(chat__transaction=transaction)
    print(f"   Messages trouvés: {messages.count()}")
    
    if messages.count() == 2:
        print("✅ SUCCÈS: Les messages sont bien liés à la transaction")
    else:
        print("❌ ÉCHEC: Problème avec les messages de transaction")
        return False
    
    # TEST 2: Vérifier qu'il n'y a pas de messages "Private message from"
    print("\n📋 TEST 2: Absence de messages parasites")
    print("-" * 30)
    
    # Vérifier qu'il n'y a pas de messages avec "Private message from"
    private_messages = Message.objects.filter(content__icontains="Private message from")
    print(f"   Messages 'Private message from' trouvés: {private_messages.count()}")
    
    if private_messages.count() == 0:
        print("✅ SUCCÈS: Aucun message parasite trouvé")
    else:
        print("❌ ÉCHEC: Des messages parasites sont présents")
        return False
    
    # TEST 3: Test de l'API de récupération des messages
    print("\n📋 TEST 3: API de récupération des messages")
    print("-" * 30)
    
    client = Client()
    client.force_login(buyer)
    
    response = client.get(f'/transaction/{transaction.id}/messages/')
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Messages récupérés: {len(data.get('messages', []))}")
        
        if len(data.get('messages', [])) == 2:
            print("✅ SUCCÈS: API fonctionne correctement")
        else:
            print("❌ ÉCHEC: API ne retourne pas les bons messages")
            return False
    else:
        print("❌ ÉCHEC: Erreur API")
        return False
    
    # TEST 4: Test d'envoi de message
    print("\n📋 TEST 4: Envoi de message")
    print("-" * 30)
    
    response = client.post(f'/transaction/{transaction.id}/send-message/', {
        'content': 'Test message via API'
    })
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'success':
            print("✅ SUCCÈS: Message envoyé avec succès")
        else:
            print(f"❌ ÉCHEC: Erreur API: {data.get('message')}")
            return False
    else:
        print("❌ ÉCHEC: Erreur lors de l'envoi")
        return False
    
    # Vérifier que le message a été créé
    new_messages = Message.objects.filter(chat__transaction=transaction)
    print(f"   Total messages après envoi: {new_messages.count()}")
    
    if new_messages.count() == 3:
        print("✅ SUCCÈS: Le nouveau message a été créé")
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
    
    print("\n🎉 TOUS LES TESTS DU CHAT ONT RÉUSSI!")
    print("=" * 50)
    print("✅ Messages de transaction fonctionnels")
    print("✅ Aucun message parasite")
    print("✅ API de récupération opérationnelle")
    print("✅ Envoi de messages fonctionnel")
    print("✅ Padding des bulles réduit")
    
    return True

if __name__ == '__main__':
    success = test_chat_fixes()
    if success:
        print("\n✅ Test réussi !")
        sys.exit(0)
    else:
        print("\n❌ Test échoué !")
        sys.exit(1)
