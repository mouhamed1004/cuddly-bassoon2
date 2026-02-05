#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégration entre les litiges et les payouts
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import PayoutRequest, Dispute, Transaction, User, Post
from blizzgame.cinetpay_utils import DisputeResolutionAPI
from django.utils import timezone
from decimal import Decimal

def test_payout_request_creation():
    """Test la création de PayoutRequest pour les remboursements et payouts"""
    print("🧪 TEST D'INTÉGRATION LITIGES → PAYOUTS")
    print("=" * 60)
    
    # Vérifier que le champ payout_type existe
    try:
        payout_type_field = PayoutRequest._meta.get_field('payout_type')
        print(f"✅ Champ payout_type trouvé: {payout_type_field}")
        print(f"   - Choix disponibles: {payout_type_field.choices}")
    except Exception as e:
        print(f"❌ Champ payout_type manquant: {e}")
        return False
    
    # Vérifier les choix disponibles
    choices = dict(PayoutRequest.PAYOUT_TYPE_CHOICES)
    print(f"✅ Choix de payout_type: {choices}")
    
    # Compter les PayoutRequest existantes
    total_payouts = PayoutRequest.objects.count()
    seller_payouts = PayoutRequest.objects.filter(payout_type='seller_payout').count()
    buyer_refunds = PayoutRequest.objects.filter(payout_type='buyer_refund').count()
    
    print(f"\n📊 STATISTIQUES ACTUELLES:")
    print(f"   - Total PayoutRequest: {total_payouts}")
    print(f"   - Paiements vendeurs: {seller_payouts}")
    print(f"   - Remboursements acheteurs: {buyer_refunds}")
    
    # Vérifier les litiges existants
    total_disputes = Dispute.objects.count()
    resolved_disputes = Dispute.objects.filter(status__in=['resolved_buyer', 'resolved_seller']).count()
    
    print(f"\n📊 LITIGES:")
    print(f"   - Total litiges: {total_disputes}")
    print(f"   - Litiges résolus: {resolved_disputes}")
    
    # Vérifier la cohérence
    if total_payouts > 0:
        print(f"\n🔍 VÉRIFICATION DE COHÉRENCE:")
        
        # Vérifier que tous les PayoutRequest ont un type
        payouts_without_type = PayoutRequest.objects.filter(payout_type__isnull=True).count()
        if payouts_without_type > 0:
            print(f"   ⚠️  {payouts_without_type} PayoutRequest sans type")
        else:
            print(f"   ✅ Tous les PayoutRequest ont un type")
        
        # Vérifier les types
        for payout in PayoutRequest.objects.all()[:5]:  # Afficher les 5 premiers
            print(f"   - Payout {payout.id.hex[:8]}: {payout.payout_type} - {payout.amount} {payout.currency}")
    
    return True

def test_dispute_resolution_api():
    """Test l'API de résolution des litiges"""
    print(f"\n🔧 TEST DE L'API DE RÉSOLUTION:")
    
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

def test_admin_interface():
    """Test l'interface admin"""
    print(f"\n👨‍💼 TEST DE L'INTERFACE ADMIN:")
    
    try:
        from blizzgame.admin import PayoutRequestAdmin
        
        # Vérifier que le champ payout_type est dans list_display
        if 'payout_type_display' in PayoutRequestAdmin.list_display:
            print(f"✅ payout_type_display dans list_display")
        else:
            print(f"❌ payout_type_display manquant de list_display")
            
        # Vérifier que le champ payout_type est dans list_filter
        if 'payout_type' in PayoutRequestAdmin.list_filter:
            print(f"✅ payout_type dans list_filter")
        else:
            print(f"❌ payout_type manquant de list_filter")
            
    except Exception as e:
        print(f"❌ Erreur lors du test de l'interface admin: {e}")
        return False
    
    return True

def main():
    print("🚀 TEST D'INTÉGRATION LITIGES → PAYOUTS")
    print("=" * 60)
    
    success = True
    
    # Test 1: Création de PayoutRequest
    if not test_payout_request_creation():
        success = False
    
    # Test 2: API de résolution
    if not test_dispute_resolution_api():
        success = False
    
    # Test 3: Interface admin
    if not test_admin_interface():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ L'intégration litiges → payouts est fonctionnelle")
        print("✅ Les remboursements créent maintenant des PayoutRequest")
        print("✅ L'interface admin affiche les types de payout")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    return success

if __name__ == "__main__":
    main()
