#!/usr/bin/env python
"""
Script pour tester la fonctionnalité de chat
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

def test_chat_functionality():
    """Teste la fonctionnalité de chat"""
    
    print("💬 Test de la fonctionnalité de chat...")
    print("=" * 50)
    
    try:
        # Créer des utilisateurs de test
        buyer, created = User.objects.get_or_create(
            username='test_buyer_chat',
            defaults={'email': 'buyer@test.com'}
        )
        
        seller, created = User.objects.get_or_create(
            username='test_seller_chat',
            defaults={'email': 'seller@test.com'}
        )
        
        # Créer un post de test
        post, created = Post.objects.get_or_create(
            title='Test Chat Functionality',
            defaults={
                'author': seller,
                'user': seller.username,
                'caption': 'Post de test pour le chat',
                'price': 20.00,
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
                'amount': 20.00,
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
            platform_commission=2.0,
            seller_amount=18.0,
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
        
        # Simuler l'envoi d'un message
        response = client.post(send_url, {
            'content': 'Bonjour, j\'ai payé pour votre article!',
            'csrfmiddlewaretoken': 'test'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        print(f"✅ Réponse envoi message: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Données JSON: {data}")
                
                if data.get('status') == 'success':
                    print("✅ Message envoyé avec succès!")
                else:
                    print(f"❌ Erreur: {data.get('message', 'Erreur inconnue')}")
            except Exception as e:
                print(f"❌ Erreur parsing JSON: {e}")
                print(f"   Contenu: {response.content}")
        else:
            print(f"❌ Code de statut inattendu: {response.status_code}")
            print(f"   Contenu: {response.content}")
        
        # Vérifier si le message a été créé
        conversation = PrivateConversation.objects.filter(
            user1=min(buyer, seller, key=lambda u: u.id),
            user2=max(buyer, seller, key=lambda u: u.id)
        ).first()
        
        if conversation:
            messages = PrivateMessage.objects.filter(conversation=conversation)
            print(f"✅ Messages dans la conversation: {messages.count()}")
            for msg in messages:
                print(f"   - {msg.sender.username}: {msg.content}")
        else:
            print("❌ Aucune conversation trouvée")
        
        # Tester la récupération des messages
        get_url = reverse('get_transaction_messages', args=[transaction.id])
        response = client.get(get_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        print(f"✅ Réponse récupération messages: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Messages récupérés: {len(data.get('messages', []))}")
            except Exception as e:
                print(f"❌ Erreur parsing JSON: {e}")
        
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
    
    print("🚀 Test de la fonctionnalité de chat")
    print("=" * 60)
    
    success = test_chat_functionality()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test terminé!")
    else:
        print("❌ Test échoué.")
    
    return success

if __name__ == '__main__':
    main()
