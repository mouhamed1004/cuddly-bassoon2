#!/usr/bin/env python
"""
Script pour tester manuellement les notifications CinetPay
Simule ce que CinetPay ferait après un paiement réussi
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order, ShopCinetPayTransaction
from blizzgame.cinetpay_utils import handle_cinetpay_notification
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_manual_notification():
    """Test manuel d'une notification CinetPay"""
    
    print("🧪 TEST MANUEL DE NOTIFICATION CINETPAY")
    print("=" * 50)
    
    # Récupérer la dernière commande
    last_order = Order.objects.order_by('-created_at').first()
    if not last_order:
        print("❌ Aucune commande trouvée")
        return
    
    print(f"📦 Commande testée: {last_order.order_number}")
    print(f"   Statut actuel: {last_order.payment_status} / {last_order.status}")
    print(f"   Montant: {last_order.total_amount}")
    
    # Vérifier s'il y a une transaction CinetPay
    try:
        cinetpay_trans = last_order.cinetpay_transaction
        print(f"💳 Transaction CinetPay: {cinetpay_trans.cinetpay_transaction_id}")
        print(f"   Statut actuel: {cinetpay_trans.status}")
        
        # Simuler une notification de succès de CinetPay
        print("\n🚀 Simulation de notification CinetPay...")
        
        # Données que CinetPay enverrait normalement
        fake_notification = {
            'cpm_trans_id': cinetpay_trans.cinetpay_transaction_id,
            'cpm_site_id': '105893977',  # Votre site ID
            'cpm_result': '00',  # Code succès CinetPay
            'cpm_trans_status': 'ACCEPTED',
            'cpm_amount': str(cinetpay_trans.amount),
            'cpm_currency': cinetpay_trans.currency,
            'cpm_payid': f"PAY_{cinetpay_trans.cinetpay_transaction_id}",
            'signature': 'fake_signature_for_test'  # En réalité, CinetPay signe les données
        }
        
        print(f"📨 Données de notification simulées:")
        for key, value in fake_notification.items():
            print(f"   {key}: {value}")
        
        # Traiter la notification
        print(f"\n⚙️  Traitement de la notification...")
        
        try:
            success = handle_cinetpay_notification(fake_notification)
            
            if success:
                print("✅ Notification traitée avec SUCCÈS!")
                
                # Recharger les données pour voir les changements
                last_order.refresh_from_db()
                cinetpay_trans.refresh_from_db()
                
                print(f"\n📦 Commande après traitement:")
                print(f"   Statut: {last_order.payment_status} / {last_order.status}")
                print(f"   Shopify Order ID: {last_order.shopify_order_id or 'Non créé'}")
                print(f"   Shopify Order Number: {last_order.shopify_order_number or 'Non créé'}")
                
                print(f"\n💳 Transaction après traitement:")
                print(f"   Statut: {cinetpay_trans.status}")
                print(f"   Complétée le: {cinetpay_trans.completed_at or 'Non complétée'}")
                
                if last_order.shopify_order_id:
                    print(f"\n🎉 SUCCÈS COMPLET!")
                    print(f"   ✅ Paiement confirmé")
                    print(f"   ✅ Commande créée sur Shopify")
                    print(f"   ✅ Statut mis à jour")
                else:
                    print(f"\n⚠️  SUCCÈS PARTIEL:")
                    print(f"   ✅ Paiement confirmé")
                    print(f"   ❌ Commande non créée sur Shopify (voir les logs)")
                    
            else:
                print("❌ Échec du traitement de la notification")
                print("   Vérifiez les logs pour plus de détails")
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement: {e}")
            import traceback
            traceback.print_exc()
            
    except ShopCinetPayTransaction.DoesNotExist:
        print("❌ Aucune transaction CinetPay associée à cette commande")
        print("   Cela signifie que l'initiation du paiement a échoué")
        
        # Afficher les transactions existantes
        all_trans = ShopCinetPayTransaction.objects.all()
        print(f"\n📊 Transactions CinetPay existantes: {all_trans.count()}")
        for trans in all_trans.order_by('-created_at')[:3]:
            print(f"   {trans.cinetpay_transaction_id}: {trans.status} - {trans.order.order_number}")

def create_test_notification_endpoint():
    """Crée un endpoint de test pour recevoir les notifications"""
    
    print(f"\n🔧 SOLUTION TEMPORAIRE:")
    print(f"1. Utilisez ngrok pour exposer votre serveur:")
    print(f"   ngrok http 8000")
    print(f"2. Copiez l'URL publique générée")
    print(f"3. Mettez à jour BASE_URL dans .env")
    print(f"4. Redémarrez votre serveur Django")
    print(f"5. Testez un nouveau paiement")

if __name__ == "__main__":
    test_manual_notification()
    create_test_notification_endpoint()
