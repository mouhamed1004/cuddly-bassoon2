#!/usr/bin/env python
"""
Test de la correction du chat
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

def test_chat_fix():
    """Test de la correction du chat"""
    
    print("🔧 Test de la correction du chat...")
    print("=" * 50)
    
    try:
        # Créer des utilisateurs de test
        buyer, created = User.objects.get_or_create(
            username='test_buyer_fix',
            defaults={'email': 'buyer@test.com'}
        )
        
        seller, created = User.objects.get_or_create(
            username='test_seller_fix',
            defaults={'email': 'seller@test.com'}
        )
        
        # Créer un post de test
        post, created = Post.objects.get_or_create(
            title='Test Chat Fix',
            defaults={
                'author': seller,
                'user': seller.username,
                'caption': 'Post de test pour correction chat',
                'price': 35.00,
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
                'amount': 35.00,
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
            platform_commission=3.5,
            seller_amount=31.5,
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
        
        # Test direct de la vue
        from blizzgame.views import send_transaction_message
        from django.http import HttpRequest
        from django.contrib.auth import get_user_model
        
        # Créer une requête simulée
        request = HttpRequest()
        request.method = 'POST'
        request.user = buyer
        request.POST = {'content': 'Test message fix'}
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        
        print("\n--- Test direct de la vue ---")
        try:
            response = send_transaction_message(request, transaction.id)
            print(f"   Type de réponse: {type(response)}")
            if hasattr(response, 'content'):
                print(f"   Contenu: {response.content}")
            if hasattr(response, 'status_code'):
                print(f"   Statut: {response.status_code}")
            
            # Vérifier que c'est bien du JSON
            import json
            try:
                data = json.loads(response.content)
                print(f"   JSON valide: {data}")
            except:
                print("   ❌ Pas du JSON valide")
                
        except Exception as e:
            print(f"   Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        # Vérifier les messages créés
        print("\n--- Vérifier les messages ---")
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
    
    print("🚀 Test de la correction du chat")
    print("=" * 60)
    
    success = test_chat_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test terminé!")
    else:
        print("❌ Test échoué.")
    
    return success

if __name__ == '__main__':
    main()
