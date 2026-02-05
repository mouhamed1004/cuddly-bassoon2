#!/usr/bin/env python3
"""
Script de test pour vérifier la cohérence des montants des payouts
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import PayoutRequest
from decimal import Decimal

def test_payout_amount_consistency():
    """Test la cohérence des montants des payouts"""
    print("🧪 TEST DE COHÉRENCE DES MONTANTS")
    print("=" * 60)
    
    try:
        # Vérifier tous les payouts
        payouts = PayoutRequest.objects.all()
        total_payouts = payouts.count()
        
        print(f"📊 PayoutRequest à vérifier: {total_payouts}")
        
        if total_payouts == 0:
            print("❌ Aucune PayoutRequest trouvée")
            return False
        
        correct_count = 0
        incorrect_count = 0
        problematic_payouts = []
        
        for payout in payouts:
            try:
                if payout.payout_type == 'seller_payout':
                    # Pour les payouts de vendeurs, vérifier que amount = 90% de original_amount
                    expected_amount = float(payout.original_amount) * 0.9
                    expected_amount_rounded = round(expected_amount, 2)
                    actual_amount = float(payout.amount)
                    
                    is_correct = abs(actual_amount - expected_amount_rounded) < 0.01
                    
                    if not is_correct:
                        problematic_payouts.append({
                            'payout': payout,
                            'actual': actual_amount,
                            'expected': expected_amount_rounded,
                            'original': float(payout.original_amount),
                            'difference': abs(actual_amount - expected_amount_rounded)
                        })
                        incorrect_count += 1
                    else:
                        correct_count += 1
                    
                elif payout.payout_type == 'buyer_refund':
                    # Pour les remboursements, vérifier que amount = original_amount (100%)
                    is_correct = payout.amount == payout.original_amount
                    
                    if not is_correct:
                        problematic_payouts.append({
                            'payout': payout,
                            'actual': float(payout.amount),
                            'expected': float(payout.original_amount),
                            'original': float(payout.original_amount),
                            'difference': abs(float(payout.amount) - float(payout.original_amount))
                        })
                        incorrect_count += 1
                    else:
                        correct_count += 1
                
            except Exception as e:
                print(f"❌ Erreur pour {payout.id.hex[:8]}: {e}")
                incorrect_count += 1
                continue
        
        print(f"\n📊 Résultats:")
        print(f"   - Corrects: {correct_count}")
        print(f"   - Incorrects: {incorrect_count}")
        print(f"   - Total: {total_payouts}")
        
        # Afficher les payouts problématiques
        if problematic_payouts:
            print(f"\n❌ PAYOUTS PROBLÉMATIQUES:")
            for item in problematic_payouts:
                payout = item['payout']
                print(f"   - {payout.id.hex[:8]} ({payout.payout_type}):")
                print(f"     Montant actuel: {item['actual']}€")
                print(f"     Montant attendu: {item['expected']}€")
                print(f"     Montant original: {item['original']}€")
                print(f"     Différence: {item['difference']:.4f}€")
        
        return incorrect_count == 0
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_amounts():
    """Test des montants spécifiques mentionnés par l'utilisateur"""
    print(f"\n🧪 TEST DES MONTANTS SPÉCIFIQUES")
    print("=" * 60)
    
    try:
        # Chercher des payouts avec des montants autour de 0.14€
        payouts_014 = PayoutRequest.objects.filter(amount__gte=0.13, amount__lte=0.15)
        print(f"📊 Payouts avec montant ~0.14€: {payouts_014.count()}")
        
        for payout in payouts_014:
            print(f"\n💰 Payout {payout.id.hex[:8]}:")
            print(f"   - Montant: {payout.amount}€")
            print(f"   - Original: {payout.original_amount}€")
            print(f"   - Type: {payout.payout_type}")
            
            if payout.payout_type == 'seller_payout':
                expected_90_percent = float(payout.original_amount) * 0.9
                expected_90_percent_rounded = round(expected_90_percent, 2)
                print(f"   - 90% de {payout.original_amount}€ = {expected_90_percent_rounded}€")
                print(f"   - Cohérent: {'✅' if abs(float(payout.amount) - expected_90_percent_rounded) < 0.01 else '❌'}")
        
        # Chercher des payouts avec des montants autour de 0.17€
        payouts_017 = PayoutRequest.objects.filter(original_amount__gte=0.16, original_amount__lte=0.18)
        print(f"\n📊 Payouts avec original ~0.17€: {payouts_017.count()}")
        
        for payout in payouts_017:
            print(f"\n💰 Payout {payout.id.hex[:8]}:")
            print(f"   - Montant: {payout.amount}€")
            print(f"   - Original: {payout.original_amount}€")
            print(f"   - Type: {payout.payout_type}")
            
            if payout.payout_type == 'seller_payout':
                expected_90_percent = float(payout.original_amount) * 0.9
                expected_90_percent_rounded = round(expected_90_percent, 2)
                print(f"   - 90% de {payout.original_amount}€ = {expected_90_percent_rounded}€")
                print(f"   - Cohérent: {'✅' if abs(float(payout.amount) - expected_90_percent_rounded) < 0.01 else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 TEST DE COHÉRENCE DES MONTANTS DES PAYOUTS")
    print("=" * 60)
    
    success = True
    
    # Test général
    if not test_payout_amount_consistency():
        success = False
    
    # Test des montants spécifiques
    if not test_specific_amounts():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Tous les montants sont cohérents")
        print("✅ Les calculs 90% sont corrects")
        print("✅ Les remboursements affichent 100%")
        print("✅ Aucun problème de cohérence détecté")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Des incohérences ont été détectées")
        print("⚠️  Il faut corriger les montants problématiques")
    
    return success

if __name__ == "__main__":
    main()
