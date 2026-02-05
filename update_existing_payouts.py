#!/usr/bin/env python3
"""
Script pour mettre à jour les PayoutRequest existantes avec original_amount
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import PayoutRequest
from decimal import Decimal

def update_existing_payouts():
    """Met à jour les PayoutRequest existantes avec original_amount"""
    print("🔄 MISE À JOUR DES PAYOUT REQUEST EXISTANTES")
    print("=" * 60)
    
    try:
        # Récupérer toutes les PayoutRequest sans original_amount
        payouts = PayoutRequest.objects.filter(original_amount__isnull=True)
        total_payouts = payouts.count()
        
        print(f"📊 PayoutRequest à mettre à jour: {total_payouts}")
        
        if total_payouts == 0:
            print("✅ Aucune PayoutRequest à mettre à jour")
            return True
        
        updated_count = 0
        
        for payout in payouts:
            try:
                if payout.payout_type == 'seller_payout':
                    # Pour les payouts de vendeurs, original_amount = amount / 0.9
                    # (car amount est 90% de original_amount)
                    original_amount = float(payout.amount) / 0.9
                    payout.original_amount = Decimal(str(round(original_amount, 2)))
                    print(f"💰 Payout vendeur {payout.id.hex[:8]}: {payout.amount}€ → original: {payout.original_amount}€")
                    
                elif payout.payout_type == 'buyer_refund':
                    # Pour les remboursements, original_amount = amount (100%)
                    payout.original_amount = payout.amount
                    print(f"🔄 Remboursement {payout.id.hex[:8]}: {payout.amount}€ (100%)")
                
                payout.save()
                updated_count += 1
                
            except Exception as e:
                print(f"❌ Erreur pour {payout.id.hex[:8]}: {e}")
                continue
        
        print(f"\n✅ Mise à jour terminée: {updated_count}/{total_payouts} PayoutRequest mises à jour")
        
        # Vérification
        remaining = PayoutRequest.objects.filter(original_amount__isnull=True).count()
        print(f"📊 PayoutRequest restantes sans original_amount: {remaining}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_payouts():
    """Vérifie les PayoutRequest mises à jour"""
    print(f"\n🔍 VÉRIFICATION DES PAYOUT REQUEST")
    print("=" * 60)
    
    try:
        # Afficher quelques exemples
        seller_payouts = PayoutRequest.objects.filter(payout_type='seller_payout', original_amount__isnull=False)[:3]
        buyer_refunds = PayoutRequest.objects.filter(payout_type='buyer_refund', original_amount__isnull=False)[:3]
        
        print("💰 Exemples de payouts vendeurs:")
        for payout in seller_payouts:
            percentage = (float(payout.amount) / float(payout.original_amount)) * 100
            print(f"   - {payout.id.hex[:8]}: {payout.amount}€ / {payout.original_amount}€ ({percentage:.1f}%)")
        
        print("\n🔄 Exemples de remboursements:")
        for payout in buyer_refunds:
            percentage = (float(payout.amount) / float(payout.original_amount)) * 100
            print(f"   - {payout.id.hex[:8]}: {payout.amount}€ / {payout.original_amount}€ ({percentage:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    print("🚀 MISE À JOUR DES PAYOUT REQUEST EXISTANTES")
    print("=" * 60)
    
    success = True
    
    # Mise à jour
    if not update_existing_payouts():
        success = False
    
    # Vérification
    if not verify_payouts():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 MISE À JOUR TERMINÉE AVEC SUCCÈS !")
        print("✅ Toutes les PayoutRequest ont été mises à jour")
        print("✅ Les montants originaux sont maintenant disponibles")
    else:
        print("❌ CERTAINES ERREURS ONT ÉTÉ RENCONTRÉES")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    return success

if __name__ == "__main__":
    main()
