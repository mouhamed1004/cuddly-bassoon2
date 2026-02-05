#!/usr/bin/env python3
"""
Script de test pour la mise à jour du statut des payouts
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import PayoutRequest
from django.utils import timezone

def test_payout_status_update():
    """Test la mise à jour du statut des payouts"""
    print("🧪 TEST DE MISE À JOUR DU STATUT DES PAYOUTS")
    print("=" * 60)
    
    try:
        # Vérifier qu'il y a des PayoutRequest
        total_payouts = PayoutRequest.objects.count()
        print(f"📊 Total des PayoutRequest: {total_payouts}")
        
        if total_payouts == 0:
            print("❌ Aucune PayoutRequest trouvée")
            return False
        
        # Afficher les statuts actuels
        pending_count = PayoutRequest.objects.filter(status='pending').count()
        processing_count = PayoutRequest.objects.filter(status='processing').count()
        completed_count = PayoutRequest.objects.filter(status='completed').count()
        failed_count = PayoutRequest.objects.filter(status='failed').count()
        
        print(f"📈 Statuts actuels:")
        print(f"   - En attente: {pending_count}")
        print(f"   - En cours: {processing_count}")
        print(f"   - Terminés: {completed_count}")
        print(f"   - Échoués: {failed_count}")
        
        # Prendre une PayoutRequest en attente pour le test
        test_payout = PayoutRequest.objects.filter(status='pending').first()
        if not test_payout:
            print("❌ Aucune PayoutRequest en attente trouvée")
            return False
        
        print(f"\n🔍 PayoutRequest de test:")
        print(f"   - ID: {test_payout.id.hex[:8]}")
        print(f"   - Statut actuel: {test_payout.status}")
        print(f"   - Type: {test_payout.payout_type}")
        print(f"   - Montant: {test_payout.amount} {test_payout.currency}")
        
        # Tester la mise à jour du statut
        print(f"\n🔄 Test de mise à jour du statut...")
        
        # Sauvegarder l'ancien statut
        old_status = test_payout.status
        
        # Changer le statut vers 'processing'
        test_payout.status = 'processing'
        test_payout.save()
        
        print(f"✅ Statut changé de '{old_status}' vers 'processing'")
        
        # Vérifier que le changement a été sauvegardé
        test_payout.refresh_from_db()
        if test_payout.status == 'processing':
            print(f"✅ Vérification: Le statut est bien 'processing'")
        else:
            print(f"❌ Erreur: Le statut n'a pas été mis à jour")
            return False
        
        # Tester le changement vers 'completed'
        test_payout.status = 'completed'
        test_payout.completed_at = timezone.now()
        test_payout.save()
        
        print(f"✅ Statut changé vers 'completed' avec completed_at")
        
        # Vérifier que completed_at a été mis à jour
        test_payout.refresh_from_db()
        if test_payout.status == 'completed' and test_payout.completed_at:
            print(f"✅ Vérification: Le statut est 'completed' et completed_at est défini")
        else:
            print(f"❌ Erreur: completed_at n'a pas été mis à jour")
            return False
        
        # Remettre le statut original pour ne pas affecter les données
        test_payout.status = old_status
        test_payout.completed_at = None
        test_payout.save()
        
        print(f"✅ Statut remis à '{old_status}' (nettoyage)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_payout_model_methods():
    """Test les méthodes du modèle PayoutRequest"""
    print(f"\n🧪 TEST DES MÉTHODES DU MODÈLE PAYOUTREQUEST")
    print("=" * 60)
    
    try:
        # Prendre une PayoutRequest pour les tests
        payout = PayoutRequest.objects.first()
        if not payout:
            print("❌ Aucune PayoutRequest trouvée")
            return False
        
        print(f"📋 PayoutRequest de test: {payout.id.hex[:8]}")
        
        # Tester get_status_display()
        status_display = payout.get_status_display()
        print(f"✅ get_status_display(): '{status_display}'")
        
        # Tester get_payout_type_display()
        type_display = payout.get_payout_type_display()
        print(f"✅ get_payout_type_display(): '{type_display}'")
        
        # Tester __str__()
        str_representation = str(payout)
        print(f"✅ __str__(): '{str_representation}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 TEST DE LA MISE À JOUR DU STATUT DES PAYOUTS")
    print("=" * 60)
    
    success = True
    
    # Test 1: Mise à jour du statut
    if not test_payout_status_update():
        success = False
    
    # Test 2: Méthodes du modèle
    if not test_payout_model_methods():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ La mise à jour du statut fonctionne")
        print("✅ Les méthodes du modèle fonctionnent")
        print("✅ Le système est prêt pour l'interface utilisateur")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    return success

if __name__ == "__main__":
    main()
