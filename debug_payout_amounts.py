#!/usr/bin/env python3
"""
Script pour déboguer les montants des payouts
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import PayoutRequest
from decimal import Decimal

def debug_payout_amounts():
    """Débogue les montants des payouts"""
    print("🔍 DÉBOGAGE DES MONTANTS DES PAYOUTS")
    print("=" * 60)
    
    try:
        # Chercher des payouts avec des montants problématiques
        payouts = PayoutRequest.objects.filter(payout_type='seller_payout').order_by('amount')
        
        print(f"📊 Payouts vendeurs trouvés: {payouts.count()}")
        
        for payout in payouts[:10]:  # Afficher les 10 premiers
            # Calcul actuel (diviser par 0.9)
            calculated_original = float(payout.amount) / 0.9
            calculated_original_rounded = round(calculated_original, 2)
            
            # Vérifier si le calcul est cohérent
            calculated_90_percent = calculated_original_rounded * 0.9
            calculated_90_percent_rounded = round(calculated_90_percent, 2)
            
            print(f"\n💰 Payout {payout.id.hex[:8]}:")
            print(f"   - Montant actuel: {payout.amount}€")
            print(f"   - Original calculé: {calculated_original:.4f}€")
            print(f"   - Original arrondi: {calculated_original_rounded}€")
            print(f"   - 90% de l'original: {calculated_90_percent:.4f}€")
            print(f"   - 90% arrondi: {calculated_90_percent_rounded}€")
            print(f"   - Cohérent: {'✅' if float(payout.amount) == calculated_90_percent_rounded else '❌'}")
            
            # Essayer de récupérer le montant original depuis la transaction
            try:
                if payout.escrow_transaction and payout.escrow_transaction.cinetpay_transaction:
                    transaction = payout.escrow_transaction.cinetpay_transaction.transaction
                    if transaction:
                        print(f"   - Montant transaction: {transaction.amount}€")
                        print(f"   - 90% de transaction: {float(transaction.amount) * 0.9:.2f}€")
                        print(f"   - Match avec payout: {'✅' if float(payout.amount) == round(float(transaction.amount) * 0.9, 2) else '❌'}")
            except Exception as e:
                print(f"   - Erreur transaction: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du débogage: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_problematic_payouts():
    """Trouve les payouts avec des incohérences"""
    print(f"\n🔍 RECHERCHE DE PAYOUTS PROBLÉMATIQUES")
    print("=" * 60)
    
    try:
        problematic_payouts = []
        
        for payout in PayoutRequest.objects.filter(payout_type='seller_payout'):
            # Calculer le montant original
            calculated_original = float(payout.amount) / 0.9
            calculated_original_rounded = round(calculated_original, 2)
            
            # Vérifier la cohérence
            calculated_90_percent = calculated_original_rounded * 0.9
            calculated_90_percent_rounded = round(calculated_90_percent, 2)
            
            if abs(float(payout.amount) - calculated_90_percent_rounded) > 0.01:
                problematic_payouts.append({
                    'payout': payout,
                    'amount': payout.amount,
                    'calculated_original': calculated_original_rounded,
                    'calculated_90_percent': calculated_90_percent_rounded,
                    'difference': abs(float(payout.amount) - calculated_90_percent_rounded)
                })
        
        print(f"📊 Payouts problématiques trouvés: {len(problematic_payouts)}")
        
        for item in problematic_payouts[:5]:  # Afficher les 5 premiers
            payout = item['payout']
            print(f"\n❌ Payout {payout.id.hex[:8]}:")
            print(f"   - Montant: {item['amount']}€")
            print(f"   - Original calculé: {item['calculated_original']}€")
            print(f"   - 90% recalculé: {item['calculated_90_percent']}€")
            print(f"   - Différence: {item['difference']:.4f}€")
        
        return problematic_payouts
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("🚀 DÉBOGAGE DES MONTANTS DES PAYOUTS")
    print("=" * 60)
    
    # Débogage général
    debug_payout_amounts()
    
    # Recherche de payouts problématiques
    problematic = find_problematic_payouts()
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if problematic:
        print(f"❌ {len(problematic)} payouts problématiques trouvés")
        print("⚠️  Il faut corriger les montants originaux")
    else:
        print("✅ Aucun payout problématique trouvé")
        print("✅ Tous les montants sont cohérents")

if __name__ == "__main__":
    main()
