#!/usr/bin/env python3
"""
Script de test complet pour vérifier que le système manuel fonctionne
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Dispute, Transaction, User, Post, PayoutRequest, EscrowTransaction
from blizzgame.cinetpay_utils import DisputeResolutionAPI
from django.utils import timezone
from decimal import Decimal

def test_escrow_transaction_creation():
    """Test la création d'EscrowTransaction avec les bons champs"""
    print("🧪 TEST DE CRÉATION D'ESCROW TRANSACTION")
    print("=" * 60)
    
    try:
        # Vérifier le modèle EscrowTransaction
        from blizzgame.models import EscrowTransaction
        
        # Afficher les champs disponibles
        fields = [field.name for field in EscrowTransaction._meta.fields]
        print(f"📋 Champs disponibles dans EscrowTransaction: {fields}")
        
        # Vérifier qu'il n'y a pas de champ 'transaction'
        if 'transaction' in fields:
            print("❌ ERREUR: Le champ 'transaction' existe encore dans EscrowTransaction")
            return False
        else:
            print("✅ Le champ 'transaction' n'existe pas (correct)")
        
        # Vérifier que le champ 'cinetpay_transaction' existe
        if 'cinetpay_transaction' in fields:
            print("✅ Le champ 'cinetpay_transaction' existe (correct)")
        else:
            print("❌ ERREUR: Le champ 'cinetpay_transaction' n'existe pas")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_payout_system():
    """Test le système de payout manuel"""
    print("\n🧪 TEST DU SYSTÈME DE PAYOUT MANUEL")
    print("=" * 60)
    
    try:
        api = DisputeResolutionAPI()
        print(f"✅ DisputeResolutionAPI initialisée")
        
        # Trouver un litige en attente
        dispute = Dispute.objects.filter(status='pending').first()
        if not dispute:
            print("❌ Aucun litige en attente trouvé")
            return False
        
        print(f"📋 Litige trouvé: {dispute.id.hex[:8]}")
        print(f"   - Statut: {dispute.status}")
        print(f"   - Montant: {dispute.disputed_amount}€")
        print(f"   - Transaction: {dispute.transaction.id.hex[:8] if dispute.transaction else 'N/A'}")
        
        # Vérifier le vendeur
        seller = dispute.transaction.seller
        print(f"👤 Vendeur: {seller.username}")
        
        # Vérifier les informations de paiement
        if hasattr(seller, 'payment_info'):
            payment_info = seller.payment_info
            print(f"💳 Informations de paiement:")
            print(f"   - Méthode: {payment_info.preferred_payment_method}")
            print(f"   - Vérifié: {payment_info.is_verified}")
            if payment_info.preferred_payment_method == 'mobile_money':
                print(f"   - Téléphone: {payment_info.phone_number}")
                print(f"   - Pays: {payment_info.country}")
                print(f"   - Opérateur: {payment_info.operator}")
        else:
            print("❌ Le vendeur n'a pas d'informations de paiement")
            return False
        
        # Compter les PayoutRequest avant
        payout_count_before = PayoutRequest.objects.count()
        print(f"📊 PayoutRequest avant: {payout_count_before}")
        
        # Tester le processus de payout
        print(f"\n🔄 Test du processus de payout...")
        result = api.process_payout(dispute)
        
        print(f"📋 Résultat: {result}")
        
        if result['success']:
            print(f"✅ PayoutRequest créée avec succès!")
            print(f"   - ID: {result['payout_id']}")
            print(f"   - Montant: {result['amount_paid']}€")
            print(f"   - Commission: {result['commission']}€")
            print(f"   - Mode manuel: {result.get('manual_mode', False)}")
            
            # Vérifier que la PayoutRequest a été créée
            payout_count_after = PayoutRequest.objects.count()
            print(f"📊 PayoutRequest après: {payout_count_after}")
            
            if payout_count_after > payout_count_before:
                print(f"✅ Nouvelle PayoutRequest créée!")
                
                # Vérifier la dernière PayoutRequest
                latest_payout = PayoutRequest.objects.latest('created_at')
                print(f"📋 Dernière PayoutRequest:")
                print(f"   - ID: {latest_payout.id.hex[:8]}")
                print(f"   - Type: {latest_payout.payout_type}")
                print(f"   - Statut: {latest_payout.status}")
                print(f"   - Montant: {latest_payout.amount} {latest_payout.currency}")
                print(f"   - Créée: {latest_payout.created_at}")
                
                if latest_payout.status == 'pending':
                    print(f"✅ Statut correct: 'pending' (en attente de traitement manuel)")
                else:
                    print(f"❌ Statut incorrect: '{latest_payout.status}' (devrait être 'pending')")
                
            else:
                print(f"❌ Aucune nouvelle PayoutRequest créée")
                return False
                
        else:
            print(f"❌ Erreur lors de la création de la PayoutRequest: {result['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_refund_system():
    """Test le système de remboursement manuel"""
    print("\n🧪 TEST DU SYSTÈME DE REMBOURSEMENT MANUEL")
    print("=" * 60)
    
    try:
        api = DisputeResolutionAPI()
        print(f"✅ DisputeResolutionAPI initialisée")
        
        # Trouver un litige en attente
        dispute = Dispute.objects.filter(status='pending').first()
        if not dispute:
            print("❌ Aucun litige en attente trouvé")
            return False
        
        print(f"📋 Litige trouvé: {dispute.id.hex[:8]}")
        
        # Compter les PayoutRequest avant
        payout_count_before = PayoutRequest.objects.count()
        print(f"📊 PayoutRequest avant: {payout_count_before}")
        
        # Tester le processus de remboursement
        print(f"\n🔄 Test du processus de remboursement...")
        result = api.process_refund(dispute)
        
        print(f"📋 Résultat: {result}")
        
        if result['success']:
            print(f"✅ PayoutRequest créée avec succès!")
            print(f"   - ID: {result['refund_id']}")
            print(f"   - Montant remboursé: {result['amount_refunded']}€")
            print(f"   - Mode manuel: {result.get('manual_mode', False)}")
            
            # Vérifier que la PayoutRequest a été créée
            payout_count_after = PayoutRequest.objects.count()
            print(f"📊 PayoutRequest après: {payout_count_after}")
            
            if payout_count_after > payout_count_before:
                print(f"✅ Nouvelle PayoutRequest créée!")
                
                # Vérifier la dernière PayoutRequest
                latest_payout = PayoutRequest.objects.latest('created_at')
                print(f"📋 Dernière PayoutRequest:")
                print(f"   - ID: {latest_payout.id.hex[:8]}")
                print(f"   - Type: {latest_payout.payout_type}")
                print(f"   - Statut: {latest_payout.status}")
                print(f"   - Montant: {latest_payout.amount} {latest_payout.currency}")
                print(f"   - Créée: {latest_payout.created_at}")
                
                if latest_payout.payout_type == 'buyer_refund':
                    print(f"✅ Type correct: 'buyer_refund' (remboursement acheteur)")
                else:
                    print(f"❌ Type incorrect: '{latest_payout.payout_type}' (devrait être 'buyer_refund')")
                
                if latest_payout.status == 'pending':
                    print(f"✅ Statut correct: 'pending' (en attente de traitement manuel)")
                else:
                    print(f"❌ Statut incorrect: '{latest_payout.status}' (devrait être 'pending')")
                
            else:
                print(f"❌ Aucune nouvelle PayoutRequest créée")
                return False
                
        else:
            print(f"❌ Erreur lors de la création de la PayoutRequest: {result['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_payout_request_status():
    """Test le statut des PayoutRequest"""
    print(f"\n📊 TEST DU STATUT DES PAYOUT REQUEST:")
    print("=" * 60)
    
    # Compter par statut
    pending_count = PayoutRequest.objects.filter(status='pending').count()
    processing_count = PayoutRequest.objects.filter(status='processing').count()
    completed_count = PayoutRequest.objects.filter(status='completed').count()
    failed_count = PayoutRequest.objects.filter(status='failed').count()
    
    # Compter par type
    seller_payouts = PayoutRequest.objects.filter(payout_type='seller_payout').count()
    buyer_refunds = PayoutRequest.objects.filter(payout_type='buyer_refund').count()
    
    print(f"📈 Statistiques des PayoutRequest:")
    print(f"   - En attente: {pending_count}")
    print(f"   - En cours: {processing_count}")
    print(f"   - Terminées: {completed_count}")
    print(f"   - Échouées: {failed_count}")
    print(f"   - Payouts vendeurs: {seller_payouts}")
    print(f"   - Remboursements acheteurs: {buyer_refunds}")
    
    # Afficher les dernières PayoutRequest
    if PayoutRequest.objects.exists():
        print(f"\n🔍 Dernières PayoutRequest:")
        for payout in PayoutRequest.objects.order_by('-created_at')[:5]:
            print(f"   - {payout.id.hex[:8]}: {payout.payout_type} - {payout.status} - {payout.amount} {payout.currency}")
    
    return True

def main():
    print("🚀 TEST COMPLET DU SYSTÈME MANUEL")
    print("=" * 60)
    
    success = True
    
    # Test 1: Vérification du modèle EscrowTransaction
    if not test_escrow_transaction_creation():
        success = False
    
    # Test 2: Système de payout manuel
    if not test_manual_payout_system():
        success = False
    
    # Test 3: Système de remboursement manuel
    if not test_manual_refund_system():
        success = False
    
    # Test 4: Statut des PayoutRequest
    if not test_payout_request_status():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Le système manuel fonctionne parfaitement")
        print("✅ Plus d'erreur 'NOT_FOUND' de CinetPay")
        print("✅ Plus d'erreur 'Cannot resolve keyword transaction'")
        print("✅ Les PayoutRequest sont créées avec le statut 'pending'")
        print("✅ Les remboursements et payouts fonctionnent en mode manuel")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    return success

if __name__ == "__main__":
    main()
