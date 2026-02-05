#!/usr/bin/env python
"""
Script de test pour le système de payouts
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Profile, Post, Transaction, CinetPayTransaction, EscrowTransaction, PayoutRequest
from decimal import Decimal

def test_payout_system():
    """Test du système de payouts"""
    print("🧪 Test du système de payouts...")
    
    # 1. Créer un utilisateur vendeur avec informations de payout
    print("\n1. Création d'un vendeur avec informations de payout...")
    seller, created = User.objects.get_or_create(
        username='test_seller_payout',
        defaults={'email': 'seller@test.com'}
    )
    if created:
        seller.set_password('test123')
        seller.save()
    
    # Mettre à jour le profil avec les informations de payout
    profile, _ = Profile.objects.get_or_create(user=seller)
    profile.payout_phone = '+225 07 12 34 56 78'
    profile.payout_country = 'CI'
    profile.payout_operator = 'Orange'
    profile.payout_verified = True
    profile.save()
    
    print(f"✅ Vendeur créé: {seller.username}")
    print(f"   - Téléphone: {profile.payout_phone}")
    print(f"   - Pays: {profile.payout_country}")
    print(f"   - Opérateur: {profile.payout_operator}")
    print(f"   - Vérifié: {profile.payout_verified}")
    
    # 2. Créer un acheteur
    print("\n2. Création d'un acheteur...")
    buyer, created = User.objects.get_or_create(
        username='test_buyer_payout',
        defaults={'email': 'buyer@test.com'}
    )
    if created:
        buyer.set_password('test123')
        buyer.save()
    
    print(f"✅ Acheteur créé: {buyer.username}")
    
    # 3. Créer une annonce
    print("\n3. Création d'une annonce...")
    post, created = Post.objects.get_or_create(
        title='Test Payout - Compte Gaming',
        author=seller,
        defaults={
            'caption': 'Compte de test pour le système de payout',
            'price': Decimal('50.00'),
            'user': 'test_user',
            'email': 'test@example.com',
            'is_on_sale': True
        }
    )
    
    print(f"✅ Annonce créée: {post.title}")
    print(f"   - Prix: {post.price} EUR")
    print(f"   - Vendeur: {post.author.username}")
    
    # 4. Créer une transaction CinetPay
    print("\n4. Création d'une transaction CinetPay...")
    import uuid
    test_transaction_id = str(uuid.uuid4())
    cinetpay_transaction, created = CinetPayTransaction.objects.get_or_create(
        customer_id=test_transaction_id,
        defaults={
            'transaction_id': test_transaction_id,
            'amount': post.price,
            'currency': 'EUR',
            'status': 'payment_received',
            'customer_name': buyer.username,
            'customer_surname': 'Test',
            'customer_phone_number': '+225 07 98 76 54 32',
            'customer_email': buyer.email,
            'customer_address': 'Test Address',
            'customer_city': 'Abidjan',
            'customer_country': 'CI',
            'customer_state': 'CI',
            'customer_zip_code': '00000',
            'seller_phone_number': '+225 07 12 34 56 78',
            'seller_country': 'CI',
            'seller_operator': 'Orange',
            'seller_amount': post.price * Decimal('0.9'),
            'platform_commission': post.price * Decimal('0.1')
        }
    )
    
    print(f"✅ Transaction CinetPay créée: {cinetpay_transaction.customer_id}")
    print(f"   - Montant: {cinetpay_transaction.amount} {cinetpay_transaction.currency}")
    print(f"   - Statut: {cinetpay_transaction.status}")
    
    # 5. Créer une transaction
    print("\n5. Création d'une transaction...")
    transaction, created = Transaction.objects.get_or_create(
        post=post,
        buyer=buyer,
        defaults={
            'amount': post.price,
            'status': 'processing'
        }
    )
    transaction.cinetpay_transaction = cinetpay_transaction
    transaction.save()
    
    print(f"✅ Transaction créée: {transaction.id}")
    print(f"   - Acheteur: {transaction.buyer.username}")
    print(f"   - Vendeur: {transaction.seller.username}")
    print(f"   - Montant: {transaction.amount} EUR")
    
    # 6. Simuler la finalisation de la transaction (création du payout)
    print("\n6. Simulation de la finalisation de la transaction...")
    
    # Créer un EscrowTransaction
    escrow_transaction, created = EscrowTransaction.objects.get_or_create(
        cinetpay_transaction=cinetpay_transaction,
        defaults={
            'amount': transaction.amount * Decimal('0.9'),  # 90% pour le vendeur
            'currency': 'EUR',
            'status': 'in_escrow'
        }
    )
    
    print(f"✅ EscrowTransaction créé: {escrow_transaction.id}")
    print(f"   - Montant: {escrow_transaction.amount} {escrow_transaction.currency}")
    print(f"   - Statut: {escrow_transaction.status}")
    
    # Créer un PayoutRequest
    payout_request, created = PayoutRequest.objects.get_or_create(
        escrow_transaction=escrow_transaction,
        defaults={
            'amount': transaction.amount * Decimal('0.9'),  # 90% pour le vendeur
            'currency': 'EUR',
            'recipient_phone': profile.payout_phone,
            'recipient_country': profile.payout_country,
            'recipient_operator': profile.payout_operator,
            'status': 'pending'
        }
    )
    
    print(f"✅ PayoutRequest créé: {payout_request.id}")
    print(f"   - Montant: {payout_request.amount} {payout_request.currency}")
    print(f"   - Téléphone: {payout_request.recipient_phone}")
    print(f"   - Pays: {payout_request.recipient_country}")
    print(f"   - Opérateur: {payout_request.recipient_operator}")
    print(f"   - Statut: {payout_request.status}")
    
    # 7. Afficher les statistiques
    print("\n7. Statistiques du système de payouts...")
    total_payouts = PayoutRequest.objects.count()
    pending_payouts = PayoutRequest.objects.filter(status='pending').count()
    processing_payouts = PayoutRequest.objects.filter(status='processing').count()
    completed_payouts = PayoutRequest.objects.filter(status='completed').count()
    failed_payouts = PayoutRequest.objects.filter(status='failed').count()
    
    print(f"📊 Statistiques:")
    print(f"   - Total payouts: {total_payouts}")
    print(f"   - En attente: {pending_payouts}")
    print(f"   - En cours: {processing_payouts}")
    print(f"   - Terminés: {completed_payouts}")
    print(f"   - Échoués: {failed_payouts}")
    
    # 8. Test de l'export CSV
    print("\n8. Test de l'export CSV...")
    try:
        from blizzgame.admin_views import export_payouts_csv
        from django.http import HttpRequest
        
        # Simuler une requête
        request = HttpRequest()
        request.user = User.objects.filter(is_superuser=True).first()
        
        if request.user:
            response = export_payouts_csv(request)
            print(f"✅ Export CSV fonctionne: {response.status_code}")
            print(f"   - Type de contenu: {response['Content-Type']}")
            print(f"   - Nom de fichier: {response['Content-Disposition']}")
        else:
            print("⚠️ Aucun superutilisateur trouvé pour tester l'export")
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'export: {e}")
    
    print("\n🎉 Test du système de payouts terminé!")
    print("\n📋 Prochaines étapes:")
    print("   1. Accédez à l'interface admin Django")
    print("   2. Allez sur 'Payout requests' pour voir les payouts")
    print("   3. Utilisez l'export CSV pour CinetPay")
    print("   4. Testez le tableau de bord des payouts")

if __name__ == '__main__':
    test_payout_system()
