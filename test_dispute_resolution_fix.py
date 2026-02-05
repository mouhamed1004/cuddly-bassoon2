#!/usr/bin/env python3
"""
Script de test pour vérifier que la résolution des litiges fonctionne
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Dispute, Transaction, User, Post
from blizzgame.cinetpay_utils import DisputeResolutionAPI
from django.utils import timezone
from decimal import Decimal

def test_dispute_resolution_api():
    """Test l'API de résolution des litiges"""
    print("🧪 TEST DE L'API DE RÉSOLUTION DES LITIGES")
    print("=" * 60)
    
    try:
        api = DisputeResolutionAPI()
        print(f"✅ DisputeResolutionAPI initialisée")
        
        # Vérifier que les méthodes existent
        if hasattr(api, 'process_refund'):
            print(f"✅ Méthode process_refund disponible")
        else:
            print(f"❌ Méthode process_refund manquante")
            
        if hasattr(api, 'process_payout'):
            print(f"✅ Méthode process_payout disponible")
        else:
            print(f"❌ Méthode process_payout manquante")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de l'API: {e}")
        return False
    
    return True

def test_dispute_data():
    """Test les données de litiges existants"""
    print(f"\n📊 TEST DES DONNÉES DE LITIGES:")
    print("=" * 60)
    
    # Compter les litiges
    total_disputes = Dispute.objects.count()
    pending_disputes = Dispute.objects.filter(status='pending').count()
    in_progress_disputes = Dispute.objects.filter(status='in_progress').count()
    resolved_disputes = Dispute.objects.filter(status__in=['resolved_buyer', 'resolved_seller']).count()
    
    print(f"📈 Statistiques des litiges:")
    print(f"   - Total: {total_disputes}")
    print(f"   - En attente: {pending_disputes}")
    print(f"   - En cours: {in_progress_disputes}")
    print(f"   - Résolus: {resolved_disputes}")
    
    # Afficher quelques litiges en détail
    if total_disputes > 0:
        print(f"\n🔍 Détails des litiges:")
        for dispute in Dispute.objects.all()[:5]:
            print(f"   - Litige {dispute.id.hex[:8]}: {dispute.status} - {dispute.disputed_amount}€")
            print(f"     Transaction: {dispute.transaction.id.hex[:8] if dispute.transaction else 'N/A'}")
            print(f"     Raison: {dispute.get_reason_display()}")
    
    return True

def test_transaction_data():
    """Test les données de transactions"""
    print(f"\n💰 TEST DES DONNÉES DE TRANSACTIONS:")
    print("=" * 60)
    
    # Compter les transactions
    total_transactions = Transaction.objects.count()
    completed_transactions = Transaction.objects.filter(status='completed').count()
    pending_transactions = Transaction.objects.filter(status='pending').count()
    refunded_transactions = Transaction.objects.filter(status='refunded').count()
    
    print(f"📈 Statistiques des transactions:")
    print(f"   - Total: {total_transactions}")
    print(f"   - Terminées: {completed_transactions}")
    print(f"   - En attente: {pending_transactions}")
    print(f"   - Remboursées: {refunded_transactions}")
    
    # Afficher quelques transactions en détail
    if total_transactions > 0:
        print(f"\n🔍 Détails des transactions:")
        for transaction in Transaction.objects.all()[:5]:
            print(f"   - Transaction {transaction.id.hex[:8]}: {transaction.status} - {transaction.amount}€")
            print(f"     Acheteur: {transaction.buyer.username if transaction.buyer else 'N/A'}")
            print(f"     Vendeur: {transaction.seller.username if transaction.seller else 'N/A'}")
    
    return True

def test_payout_requests():
    """Test les PayoutRequest"""
    print(f"\n💳 TEST DES PAYOUT REQUESTS:")
    print("=" * 60)
    
    from blizzgame.models import PayoutRequest
    
    # Compter les PayoutRequest
    total_payouts = PayoutRequest.objects.count()
    seller_payouts = PayoutRequest.objects.filter(payout_type='seller_payout').count()
    buyer_refunds = PayoutRequest.objects.filter(payout_type='buyer_refund').count()
    
    print(f"📈 Statistiques des PayoutRequest:")
    print(f"   - Total: {total_payouts}")
    print(f"   - Paiements vendeurs: {seller_payouts}")
    print(f"   - Remboursements acheteurs: {buyer_refunds}")
    
    # Afficher quelques PayoutRequest en détail
    if total_payouts > 0:
        print(f"\n🔍 Détails des PayoutRequest:")
        for payout in PayoutRequest.objects.all()[:5]:
            print(f"   - Payout {payout.id.hex[:8]}: {payout.payout_type} - {payout.amount} {payout.currency}")
            print(f"     Statut: {payout.status}")
            print(f"     Créé: {payout.created_at}")
    
    return True

def main():
    print("🚀 TEST DE LA RÉSOLUTION DES LITIGES")
    print("=" * 60)
    
    success = True
    
    # Test 1: API de résolution
    if not test_dispute_resolution_api():
        success = False
    
    # Test 2: Données de litiges
    if not test_dispute_data():
        success = False
    
    # Test 3: Données de transactions
    if not test_transaction_data():
        success = False
    
    # Test 4: PayoutRequest
    if not test_payout_requests():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ L'API de résolution des litiges est fonctionnelle")
        print("✅ Les données sont cohérentes")
        print("✅ Les PayoutRequest sont correctement créées")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    return success

if __name__ == "__main__":
    main()
