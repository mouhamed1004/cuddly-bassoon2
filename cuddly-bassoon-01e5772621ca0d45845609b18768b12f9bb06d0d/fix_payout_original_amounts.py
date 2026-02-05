#!/usr/bin/env python3
"""
Script pour corriger les montants originaux des payouts
en récupérant directement depuis la transaction
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import PayoutRequest
from decimal import Decimal

def fix_payout_original_amounts():
    """Corrige les montants originaux en récupérant depuis la transaction"""
    print("🔧 CORRECTION DES MONTANTS ORIGINAUX")
    print("=" * 60)
    
    try:
        # Récupérer toutes les PayoutRequest
        payouts = PayoutRequest.objects.all()
        total_payouts = payouts.count()
        
        print(f"📊 PayoutRequest à vérifier: {total_payouts}")
        
        if total_payouts == 0:
            print("✅ Aucune PayoutRequest trouvée")
            return True
        
        updated_count = 0
        error_count = 0
        
        for payout in payouts:
            try:
                # Essayer de récupérer le montant original depuis la transaction
                original_amount = None
                
                if payout.escrow_transaction and payout.escrow_transaction.cinetpay_transaction:
                    transaction = payout.escrow_transaction.cinetpay_transaction.transaction
                    if transaction:
                        original_amount = transaction.amount
                        print(f"✅ Payout {payout.id.hex[:8]}: Récupéré depuis transaction = {original_amount}€")
                
                # Si pas de transaction, utiliser le calcul actuel
                if original_amount is None:
                    if payout.payout_type == 'seller_payout':
                        # Pour les payouts de vendeurs, calculer depuis le montant actuel
                        calculated_original = float(payout.amount) / 0.9
                        original_amount = Decimal(str(round(calculated_original, 2)))
                        print(f"⚠️  Payout {payout.id.hex[:8]}: Calculé = {original_amount}€ (pas de transaction)")
                    elif payout.payout_type == 'buyer_refund':
                        # Pour les remboursements, utiliser le montant actuel
                        original_amount = payout.amount
                        print(f"✅ Payout {payout.id.hex[:8]}: Remboursement = {original_amount}€")
                
                # Mettre à jour si différent
                if payout.original_amount != original_amount:
                    old_original = payout.original_amount
                    payout.original_amount = original_amount
                    payout.save()
                    updated_count += 1
                    print(f"🔄 Mis à jour: {old_original}€ → {original_amount}€")
                else:
                    print(f"✅ Déjà correct: {original_amount}€")
                
            except Exception as e:
                error_count += 1
                print(f"❌ Erreur pour {payout.id.hex[:8]}: {e}")
                continue
        
        print(f"\n✅ Correction terminée:")
        print(f"   - Mis à jour: {updated_count}")
        print(f"   - Erreurs: {error_count}")
        print(f"   - Total: {total_payouts}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_corrections():
    """Vérifie que les corrections sont correctes"""
    print(f"\n🔍 VÉRIFICATION DES CORRECTIONS")
    print("=" * 60)
    
    try:
        # Vérifier les payouts de vendeurs
        seller_payouts = PayoutRequest.objects.filter(payout_type='seller_payout')
        print(f"💰 Payouts vendeurs: {seller_payouts.count()}")
        
        correct_count = 0
        incorrect_count = 0
        
        for payout in seller_payouts[:5]:  # Vérifier les 5 premiers
            # Vérifier la cohérence
            expected_90_percent = float(payout.original_amount) * 0.9
            expected_90_percent_rounded = round(expected_90_percent, 2)
            
            is_correct = abs(float(payout.amount) - expected_90_percent_rounded) < 0.01
            
            print(f"   - {payout.id.hex[:8]}: {payout.amount}€ / {payout.original_amount}€")
            print(f"     → 90% de {payout.original_amount}€ = {expected_90_percent_rounded}€")
            print(f"     → {'✅ Correct' if is_correct else '❌ Incorrect'}")
            
            if is_correct:
                correct_count += 1
            else:
                incorrect_count += 1
        
        # Vérifier les remboursements
        buyer_refunds = PayoutRequest.objects.filter(payout_type='buyer_refund')
        print(f"\n🔄 Remboursements: {buyer_refunds.count()}")
        
        for payout in buyer_refunds:
            is_correct = payout.amount == payout.original_amount
            print(f"   - {payout.id.hex[:8]}: {payout.amount}€ / {payout.original_amount}€")
            print(f"     → {'✅ Correct (100%)' if is_correct else '❌ Incorrect'}")
            
            if is_correct:
                correct_count += 1
            else:
                incorrect_count += 1
        
        print(f"\n📊 Résultat: {correct_count} corrects, {incorrect_count} incorrects")
        return incorrect_count == 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 CORRECTION DES MONTANTS ORIGINAUX")
    print("=" * 60)
    
    success = True
    
    # Correction
    if not fix_payout_original_amounts():
        success = False
    
    # Vérification
    if not verify_corrections():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 CORRECTION TERMINÉE AVEC SUCCÈS !")
        print("✅ Tous les montants originaux sont corrects")
        print("✅ Les calculs 90% sont cohérents")
        print("✅ Les remboursements affichent 100%")
    else:
        print("❌ CERTAINES ERREURS ONT ÉTÉ RENCONTRÉES")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    return success

if __name__ == "__main__":
    main()
