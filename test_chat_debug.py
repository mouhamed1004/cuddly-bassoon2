#!/usr/bin/env python
"""
Script de debug pour le chat
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from blizzgame.models import Post, Transaction, CinetPayTransaction, PrivateConversation, PrivateMessage

def test_chat_debug():
    """Debug du chat"""
    
    print("🔍 Debug du chat...")
    print("=" * 50)
    
    try:
        # Créer des utilisateurs de test
        buyer, created = User.objects.get_or_create(
            username='test_buyer_debug',
            defaults={'email': 'buyer@test.com'}
        )
        
        seller, created = User.objects.get_or_create(
            username='test_seller_debug',
            defaults={'email': 'seller@test.com'}
        )
        
        # Créer un post de test
        post, created = Post.objects.get_or_create(
            title='Test Chat Debug',
            defaults={
                'author': seller,
                'user': seller.username,
                'caption': 'Post de test pour debug',
                'price': 25.00,
                'game_type': 'FreeFire',
                'is_on_sale': True,
                'email': 'test@example.com',
                'password': 'test123'
            }
        )
        
        # Créer une transaction
        transaction, created = Transaction.objects.get_or_create(
            buyer=buyer,
            seller=seller,
            post=post,
            defaults={
                'amount': 25.00,
                'status': 'pending'
            }
        )
        
        # Simuler un paiement CinetPay
        cinetpay_transaction = CinetPayTransaction.objects.create(
            transaction=transaction,
            customer_id=str(buyer.id),
            customer_name='Test',
            customer_surname='User',
            customer_phone_number='+221701234567',
            customer_email=buyer.email,
            customer_address='Test',
            customer_city='Dakar',
            customer_country='SN',
            customer_state='DK',
            customer_zip_code='10000',
            amount=float(transaction.amount),
            currency='XOF',
            platform_commission=2.5,
            seller_amount=22.5,
            seller_phone_number='+221701234568',
            seller_country='SN',
            seller_operator='orange_money',
            status='payment_received',
            cinetpay_transaction_id=f"TEST_{transaction.id}",
            payment_url='https://test.cinetpay.com',
            payment_token='test_token',
            payment_received_at=timezone.now()
        )
        
        # Mettre à jour le statut
        transaction.status = 'processing'
        transaction.save()
        
        print(f"✅ Transaction créée: {transaction.id}")
        print(f"   Statut: {transaction.status}")
        print(f"   Paiement CinetPay: {cinetpay_transaction.status}")
        
        # Tester l'envoi de message
        client = Client()
        client.force_login(buyer)
        
        # Tester l'URL d'envoi de message
        send_url = reverse('send_transaction_message', args=[transaction.id])
        print(f"✅ URL d'envoi: {send_url}")
        
        # Test 1: Requête POST sans AJAX
        print("\n--- Test 1: Requête POST sans AJAX ---")
        response = client.post(send_url, {
            'content': 'Test message sans AJAX',
            'csrfmiddlewaretoken': 'test'
        })
        print(f"   Statut: {response.status_code}")
        print(f"   Type: {type(response)}")
        if hasattr(response, 'url'):
            print(f"   URL de redirection: {response.url}")
        
        # Test 2: Requête POST avec AJAX
        print("\n--- Test 2: Requête POST avec AJAX ---")
        response = client.post(send_url, {
            'content': 'Test message avec AJAX',
            'csrfmiddlewaretoken': 'test'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        print(f"   Statut: {response.status_code}")
        print(f"   Type: {type(response)}")
        if hasattr(response, 'content'):
            print(f"   Contenu: {response.content}")
        
        # Test 3: Vérifier les messages créés
        print("\n--- Test 3: Vérifier les messages ---")
        conversation = PrivateConversation.objects.filter(
            user1=min(buyer, seller, key=lambda u: u.id),
            user2=max(buyer, seller, key=lambda u: u.id)
        ).first()
        
        if conversation:
            messages = PrivateMessage.objects.filter(conversation=conversation)
            print(f"   Messages trouvés: {messages.count()}")
            for msg in messages:
                print(f"   - {msg.sender.username}: {msg.content}")
        else:
            print("   Aucune conversation trouvée")
        
        # Test 4: Vérifier la page de transaction
        print("\n--- Test 4: Page de transaction ---")
        detail_url = reverse('transaction_detail', args=[transaction.id])
        response = client.get(detail_url)
        print(f"   Statut: {response.status_code}")
        
        # Nettoyer
        transaction.delete()
        post.delete()
        buyer.delete()
        seller.delete()
        
        print("✅ Test terminé et nettoyé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    
    print("🚀 Debug du chat")
    print("=" * 60)
    
    success = test_chat_debug()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Debug terminé!")
    else:
        print("❌ Debug échoué.")
    
    return success

if __name__ == '__main__':
    main()
