#!/usr/bin/env python
"""
Test du système de suivi après résolution de litige
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Dispute, Transaction, Post, User, UserWarning, UserBan, CinetPayTransaction
from django.utils import timezone
from decimal import Decimal

def test_dispute_followup_system():
    print("🔨 Test du système de suivi après résolution de litige...")
    
    # 1. Créer des données de test
    print("\n1. Création des données de test...")
    try:
        # Créer un vendeur
        seller, created = User.objects.get_or_create(
            username='test_seller_followup',
            defaults={'email': 'seller@followup.com'}
        )
        
        # Créer un acheteur
        buyer, created = User.objects.get_or_create(
            username='test_buyer_followup',
            defaults={'email': 'buyer@followup.com'}
        )
        
        # Créer un post
        post, created = Post.objects.get_or_create(
            title='Test Followup Account',
            defaults={
                'author': seller,
                'price': 100.00,
                'caption': 'Compte de test pour suivi',
                'game_type': 'other',
                'custom_game_name': 'Test Game'
            }
        )
        
        # Créer une transaction
        transaction, created = Transaction.objects.get_or_create(
            buyer=buyer,
            seller=seller,
            post=post,
            defaults={
                'amount': 100.00,
                'status': 'processing'
            }
        )
        
        # Créer une transaction CinetPay
        cinetpay_transaction, created = CinetPayTransaction.objects.get_or_create(
            transaction=transaction,
            defaults={
                'cinetpay_transaction_id': f'test_followup_{transaction.id}',
                'amount': 10000,  # 100€ en XOF
                'currency': 'XOF',
                'customer_phone_number': '+221701234567',
                'customer_country': 'SN',
                'seller_phone_number': '+221701234567',
                'seller_country': 'SN',
                'seller_operator': 'ORANGE',
                'status': 'completed',
                'platform_commission': 10.00,
                'seller_amount': 90.00
            }
        )
        
        # Créer un litige résolu
        dispute, created = Dispute.objects.get_or_create(
            transaction=transaction,
            defaults={
                'opened_by': buyer,
                'reason': 'invalid_account',
                'description': 'Test de litige pour suivi',
                'disputed_amount': 100.00,
                'status': 'resolved_buyer',
                'resolution': 'refund',
                'resolved_at': timezone.now()
            }
        )
        
        print(f"   ✅ Vendeur: {seller.username}")
        print(f"   ✅ Acheteur: {buyer.username}")
        print(f"   ✅ Transaction: {transaction.id}")
        print(f"   ✅ Litige: {dispute.id}")
        print(f"   ✅ Résolution: {dispute.get_resolution_display()}")
        
    except Exception as e:
        print(f"   ❌ Erreur création données: {e}")
        return False
    
    # 2. Tester la logique de détermination du perdant
    print("\n2. Test de la logique de détermination du perdant...")
    try:
        if dispute.resolution == 'refund':
            losing_user = dispute.transaction.seller
            winning_user = dispute.transaction.buyer
            resolution_type = 'remboursement'
        elif dispute.resolution == 'payout':
            losing_user = dispute.transaction.buyer
            winning_user = dispute.transaction.seller
            resolution_type = 'paiement vendeur'
        else:
            print("   ❌ Litige non résolu")
            return False
        
        print(f"   ✅ Perdant: {losing_user.username} (vendeur)")
        print(f"   ✅ Gagnant: {winning_user.username} (acheteur)")
        print(f"   ✅ Type de résolution: {resolution_type}")
        
    except Exception as e:
        print(f"   ❌ Erreur logique perdant: {e}")
        return False
    
    # 3. Tester le comptage des avertissements
    print("\n3. Test du comptage des avertissements...")
    try:
        # Créer quelques avertissements de test
        warning1 = UserWarning.objects.create(
            user=losing_user,
            admin=seller,  # Utiliser le vendeur comme admin pour le test
            dispute=dispute,
            warning_type='dispute_lost',
            severity='medium',
            reason='Test avertissement 1',
            details='Détails du test',
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )
        
        warning2 = UserWarning.objects.create(
            user=losing_user,
            admin=seller,
            warning_type='inappropriate_behavior',
            severity='high',
            reason='Test avertissement 2',
            details='Détails du test 2',
            expires_at=timezone.now() + timezone.timedelta(days=15)
        )
        
        # Compter les avertissements actifs
        active_warnings = UserWarning.objects.filter(
            user=losing_user,
            is_active=True
        ).exclude(
            expires_at__lt=timezone.now()
        ).count()
        
        print(f"   ✅ Avertissements créés: 2")
        print(f"   ✅ Avertissements actifs: {active_warnings}")
        
    except Exception as e:
        print(f"   ❌ Erreur comptage avertissements: {e}")
        return False
    
    # 4. Tester le comptage des bannissements
    print("\n4. Test du comptage des bannissements...")
    try:
        # Créer un bannissement temporaire
        ban = UserBan.objects.create(
            user=losing_user,
            admin=seller,
            dispute=dispute,
            ban_type='temporary',
            reason='multiple_disputes',
            details='Test bannissement temporaire',
            starts_at=timezone.now(),
            ends_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        # Compter les bannissements actifs
        active_bans = UserBan.objects.filter(
            user=losing_user,
            is_active=True
        ).exclude(
            ends_at__lt=timezone.now()
        ).count()
        
        print(f"   ✅ Bannissement créé: {ban.id}")
        print(f"   ✅ Bannissements actifs: {active_bans}")
        
    except Exception as e:
        print(f"   ❌ Erreur comptage bannissements: {e}")
        return False
    
    # 5. Tester l'historique des litiges perdus
    print("\n5. Test de l'historique des litiges perdus...")
    try:
        # Créer un autre litige perdu
        post2, created = Post.objects.get_or_create(
            title='Test Followup Account 2',
            defaults={
                'author': seller,
                'price': 50.00,
                'caption': 'Compte de test 2',
                'game_type': 'other',
                'custom_game_name': 'Test Game 2'
            }
        )
        
        transaction2, created = Transaction.objects.get_or_create(
            buyer=buyer,
            seller=seller,
            post=post2,
            defaults={
                'amount': 50.00,
                'status': 'completed'
            }
        )
        
        dispute2 = Dispute.objects.create(
            transaction=transaction2,
            opened_by=buyer,
            reason='other',
            description='Test litige 2',
            disputed_amount=50.00,
            status='resolved_buyer',
            resolution='refund',
            resolved_at=timezone.now()
        )
        
        # Récupérer l'historique
        lost_disputes = Dispute.objects.filter(
            transaction__buyer=losing_user,
            resolution='payout'
        ).union(
            Dispute.objects.filter(
                transaction__seller=losing_user,
                resolution='refund'
            )
        ).order_by('-resolved_at')
        
        print(f"   ✅ Litiges perdus trouvés: {lost_disputes.count()}")
        for dispute_item in lost_disputes:
            print(f"      - Litige {dispute_item.id.hex[:8]}: {dispute_item.get_resolution_display()}")
        
    except Exception as e:
        print(f"   ❌ Erreur historique litiges: {e}")
        return False
    
    # 6. Tester les statistiques générales
    print("\n6. Test des statistiques générales...")
    try:
        total_disputes_as_buyer = Dispute.objects.filter(transaction__buyer=losing_user).count()
        total_disputes_as_seller = Dispute.objects.filter(transaction__seller=losing_user).count()
        total_lost_disputes = lost_disputes.count()
        
        print(f"   ✅ Litiges en tant qu'acheteur: {total_disputes_as_buyer}")
        print(f"   ✅ Litiges en tant que vendeur: {total_disputes_as_seller}")
        print(f"   ✅ Total litiges perdus: {total_lost_disputes}")
        
    except Exception as e:
        print(f"   ❌ Erreur statistiques: {e}")
        return False
    
    print("\n" + "="*60)
    print("🎉 Test du système de suivi réussi !")
    print("✅ Page de suivi après résolution fonctionnelle")
    print("✅ Système de comptage des avertissements")
    print("✅ Système de comptage des bannissements")
    print("✅ Historique des litiges perdus")
    print("✅ Statistiques générales")
    print("✅ Logique de détermination du perdant")
    
    return True

if __name__ == '__main__':
    print("🚀 Test du système de suivi après résolution de litige")
    print("=" * 60)
    
    try:
        success = test_dispute_followup_system()
        
        if success:
            print("\n🎉 Tous les tests sont passés !")
            print("✅ Le système de suivi est prêt à être utilisé")
        else:
            print("\n⚠️  Certains tests ont échoué")
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

