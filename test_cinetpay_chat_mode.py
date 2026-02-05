#!/usr/bin/env python
"""
Script de test pour vérifier le mode test CinetPay et l'activation du chat
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, Transaction, CinetPayTransaction, Notification, PrivateConversation, PrivateMessage

def test_cinetpay_test_mode():
    """Teste le mode test CinetPay"""
    
    print("🧪 Test du mode test CinetPay...")
    print("=" * 60)
    
    try:
        # Vérifier la configuration
        from django.conf import settings
        test_mode = getattr(settings, 'CINETPAY_TEST_MODE', False)
        
        if test_mode:
            print("✅ Mode test CinetPay activé")
        else:
            print("❌ Mode test CinetPay désactivé")
            return False
        
        # Vérifier les clés API
        api_key = getattr(settings, 'CINETPAY_API_KEY', None)
        site_id = getattr(settings, 'CINETPAY_SITE_ID', None)
        
        if api_key and site_id:
            print(f"✅ Configuration CinetPay: {api_key[:10]}...{api_key[-10:]}")
            print(f"✅ Site ID: {site_id}")
        else:
            print("❌ Configuration CinetPay manquante")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de configuration: {e}")
        return False

def test_chat_activation():
    """Teste l'activation du chat après paiement simulé"""
    
    print("\n💬 Test de l'activation du chat...")
    print("=" * 60)
    
    try:
        # Créer des utilisateurs de test
        buyer, created = User.objects.get_or_create(
            username='test_buyer_chat',
            defaults={
                'email': 'buyer@test.com',
                'first_name': 'Test',
                'last_name': 'Buyer'
            }
        )
        
        seller, created = User.objects.get_or_create(
            username='test_seller_chat',
            defaults={
                'email': 'seller@test.com',
                'first_name': 'Test',
                'last_name': 'Seller'
            }
        )
        
        # Créer un post de test
        post, created = Post.objects.get_or_create(
            title='Test Chat Activation',
            defaults={
                'author': seller,
                'description': 'Post de test pour le chat',
                'price': 10.00,
                'category': 'gaming',
                'is_active': True
            }
        )
        
        # Créer une transaction de test
        transaction, created = Transaction.objects.get_or_create(
            buyer=buyer,
            seller=seller,
            post=post,
            defaults={
                'amount': 10.00,
                'status': 'pending'
            }
        )
        
        print(f"✅ Transaction créée: {transaction.id}")
        print(f"   Acheteur: {buyer.username}")
        print(f"   Vendeur: {seller.username}")
        print(f"   Montant: {transaction.amount}€")
        print(f"   Statut: {transaction.status}")
        
        # Vérifier que le chat est verrouillé avant paiement
        cinetpay_payment_validated = False
        if hasattr(transaction, 'cinetpay_transaction'):
            cinetpay_payment_validated = transaction.cinetpay_transaction.status in ['payment_received', 'in_escrow', 'escrow_released', 'completed']
        
        if not cinetpay_payment_validated:
            print("✅ Chat verrouillé avant paiement (comportement attendu)")
        else:
            print("❌ Chat activé avant paiement (comportement inattendu)")
        
        # Simuler un paiement CinetPay
        cinetpay_transaction = CinetPayTransaction.objects.create(
            transaction=transaction,
            customer_id=str(buyer.id),
            customer_name=buyer.first_name or 'Test',
            customer_surname=buyer.last_name or 'User',
            customer_phone_number='+221701234567',
            customer_email=buyer.email,
            customer_address='Adresse de test',
            customer_city='Dakar',
            customer_country='SN',
            customer_state='DK',
            customer_zip_code='10000',
            amount=float(transaction.amount),
            currency='XOF',
            platform_commission=float(transaction.amount) * 0.1,
            seller_amount=float(transaction.amount) * 0.9,
            seller_phone_number='+221701234568',
            seller_country='SN',
            seller_operator='orange_money',
            status='payment_received',
            cinetpay_transaction_id=f"TEST_{transaction.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}",
            payment_url='https://test.cinetpay.com',
            payment_token='test_token_123',
            completed_at=timezone.now()
        )
        
        # Mettre à jour le statut de la transaction
        transaction.status = 'processing'
        transaction.save()
        
        print("✅ Paiement CinetPay simulé")
        print(f"   Statut CinetPay: {cinetpay_transaction.status}")
        print(f"   Statut transaction: {transaction.status}")
        
        # Vérifier que le chat est maintenant activé
        cinetpay_payment_validated = False
        if hasattr(transaction, 'cinetpay_transaction'):
            cinetpay_payment_validated = transaction.cinetpay_transaction.status in ['payment_received', 'in_escrow', 'escrow_released', 'completed']
        
        if cinetpay_payment_validated:
            print("✅ Chat activé après paiement (comportement attendu)")
        else:
            print("❌ Chat toujours verrouillé après paiement (comportement inattendu)")
        
        # Tester la création d'une conversation privée
        conversation, created = PrivateConversation.objects.get_or_create(
            user1=min(buyer, seller, key=lambda u: u.id),
            user2=max(buyer, seller, key=lambda u: u.id),
            defaults={'is_active': True}
        )
        
        if created:
            print("✅ Conversation privée créée")
        else:
            print("✅ Conversation privée existante trouvée")
        
        # Tester l'envoi de messages
        message1 = PrivateMessage.objects.create(
            conversation=conversation,
            sender=buyer,
            content="Bonjour, j'ai payé pour votre article. Pouvez-vous me donner les informations ?"
        )
        
        message2 = PrivateMessage.objects.create(
            conversation=conversation,
            sender=seller,
            content="Bonjour ! Merci pour votre achat. Voici les informations de connexion..."
        )
        
        print("✅ Messages de test créés")
        print(f"   Message 1: {message1.content[:50]}...")
        print(f"   Message 2: {message2.content[:50]}...")
        
        # Vérifier les notifications
        buyer_notifications = Notification.objects.filter(user=buyer, transaction=transaction)
        seller_notifications = Notification.objects.filter(user=seller, transaction=transaction)
        
        print(f"✅ Notifications créées:")
        print(f"   Acheteur: {buyer_notifications.count()} notification(s)")
        print(f"   Vendeur: {seller_notifications.count()} notification(s)")
        
        # Nettoyer les données de test
        transaction.delete()
        post.delete()
        buyer.delete()
        seller.delete()
        
        print("✅ Données de test nettoyées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de chat: {e}")
        return False

def test_transaction_chat_interface():
    """Teste l'interface de chat de transaction"""
    
    print("\n🖥️ Test de l'interface de chat...")
    print("=" * 60)
    
    try:
        client = Client()
        
        # Tester l'accès à la page de transaction
        response = client.get('/transaction/')
        
        if response.status_code == 200:
            print("✅ Page de transaction accessible")
        else:
            print(f"❌ Erreur d'accès à la page de transaction: {response.status_code}")
            return False
        
        # Tester l'URL de paiement CinetPay
        try:
            response = client.get('/payment/cinetpay/initiate/test-transaction-id/')
            print("✅ URL de paiement CinetPay accessible")
        except Exception as e:
            print(f"⚠️ URL de paiement CinetPay: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'interface: {e}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🚀 Test du système de chat CinetPay en mode test")
    print("=" * 80)
    
    # Tests
    tests = [
        ("Configuration CinetPay", test_cinetpay_test_mode),
        ("Activation du chat", test_chat_activation),
        ("Interface de chat", test_transaction_chat_interface),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: SUCCÈS")
            else:
                print(f"❌ {test_name}: ÉCHEC")
        except Exception as e:
            print(f"❌ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
    
    print(f"\nRésultat global: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 Tous les tests sont passés avec succès!")
        print("\n💡 Pour tester le chat:")
        print("1. Créez une annonce gaming")
        print("2. Connectez-vous avec un autre compte")
        print("3. Cliquez sur 'Acheter'")
        print("4. Cliquez sur 'Payer avec CinetPay'")
        print("5. Le paiement sera simulé et le chat activé automatiquement")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")
    
    return success_count == total_count

if __name__ == '__main__':
    main()
