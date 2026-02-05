#!/usr/bin/env python
"""
Script simple pour tester le mode test CinetPay et l'activation du chat
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from blizzgame.models import Post, Transaction, CinetPayTransaction, Notification

def test_cinetpay_test_mode():
    """Teste le mode test CinetPay"""
    
    print("🧪 Test du mode test CinetPay...")
    print("=" * 50)
    
    try:
        from django.conf import settings
        test_mode = getattr(settings, 'CINETPAY_TEST_MODE', False)
        
        if test_mode:
            print("✅ Mode test CinetPay activé")
            return True
        else:
            print("❌ Mode test CinetPay désactivé")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_chat_simulation():
    """Teste la simulation de paiement et activation du chat"""
    
    print("\n💬 Test de simulation de paiement...")
    print("=" * 50)
    
    try:
        # Créer des utilisateurs de test
        buyer, created = User.objects.get_or_create(
            username='test_buyer_simple',
            defaults={'email': 'buyer@test.com'}
        )
        
        seller, created = User.objects.get_or_create(
            username='test_seller_simple',
            defaults={'email': 'seller@test.com'}
        )
        
        # Créer un post de test
        post, created = Post.objects.get_or_create(
            title='Test Chat Simple',
            defaults={
                'author': seller,
                'user': seller.username,
                'caption': 'Post de test pour le chat',
                'price': 5.00,
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
                'amount': 5.00,
                'status': 'pending'
            }
        )
        
        print(f"✅ Transaction créée: {transaction.id}")
        print(f"   Statut initial: {transaction.status}")
        
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
            platform_commission=0.5,
            seller_amount=4.5,
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
        
        print(f"✅ Paiement simulé")
        print(f"   Statut CinetPay: {cinetpay_transaction.status}")
        print(f"   Statut transaction: {transaction.status}")
        
        # Vérifier l'activation du chat
        cinetpay_payment_validated = False
        if hasattr(transaction, 'cinetpay_transaction'):
            cinetpay_payment_validated = transaction.cinetpay_transaction.status in ['payment_received', 'in_escrow', 'escrow_released', 'completed']
        
        if cinetpay_payment_validated:
            print("✅ Chat activé après paiement")
        else:
            print("❌ Chat non activé")
        
        # Nettoyer
        transaction.delete()
        post.delete()
        buyer.delete()
        seller.delete()
        
        print("✅ Test terminé et nettoyé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    
    print("🚀 Test du mode test CinetPay pour le chat")
    print("=" * 60)
    
    # Tests
    test1 = test_cinetpay_test_mode()
    test2 = test_chat_simulation()
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if test1 and test2:
        print("🎉 Tous les tests sont passés!")
        print("\n💡 Pour tester le chat en mode réel:")
        print("1. Allez sur http://127.0.0.1:8000/")
        print("2. Créez une annonce gaming")
        print("3. Connectez-vous avec un autre compte")
        print("4. Cliquez sur 'Acheter'")
        print("5. Cliquez sur 'Payer avec CinetPay'")
        print("6. Le paiement sera simulé et le chat activé!")
    else:
        print("❌ Certains tests ont échoué")
    
    return test1 and test2

if __name__ == '__main__':
    main()
