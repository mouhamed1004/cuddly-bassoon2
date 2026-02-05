#!/usr/bin/env python3
"""
Script pour tester les méthodes de paiement CinetPay
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order, ShopCinetPayTransaction
from blizzgame.cinetpay_utils import CinetPayAPI
from blizzgame.currency_service import CurrencyService
from django.conf import settings
import requests

def test_payment_methods():
    """Teste différentes méthodes de paiement et montants"""
    print("TEST METHODES DE PAIEMENT CINETPAY")
    print("=" * 50)
    
    try:
        # 1. Créer des transactions avec différents montants
        print("\n1. TEST DIFFERENTS MONTANTS")
        print("-" * 40)
        
        # Prendre une commande en attente pour les tests
        pending_orders = Order.objects.filter(payment_status='pending').order_by('-created_at')
        if not pending_orders.exists():
            print("Aucune commande en attente pour tester")
            return False
        
        test_order = pending_orders.first()
        print(f"Commande de test: #{test_order.order_number}")
        
        # Données client de test
        customer_data = {
            'customer_name': 'TestAmount',
            'customer_surname': 'User',
            'customer_email': 'testamount@blizz.com',
            'customer_phone_number': '+221701234567',
            'customer_address': '123 Test Street',
            'customer_city': 'Dakar',
            'customer_country': 'SN',
            'customer_state': 'Dakar',
            'customer_zip_code': '10000',
        }
        
        # Tester différents montants en euros et leur conversion
        test_amounts_eur = [0.16, 1.0, 5.0, 10.0, 20.0]
        
        cinetpay_api = CinetPayAPI()
        
        for amount_eur in test_amounts_eur:
            print(f"\nTest montant: {amount_eur}€")
            
            # Convertir en XOF
            amount_xof = CurrencyService.convert_amount(amount_eur, 'EUR', 'XOF')
            print(f"  Converti: {amount_xof} XOF")
            
            # Supprimer les anciennes transactions de test
            ShopCinetPayTransaction.objects.filter(order=test_order).delete()
            
            # Créer une copie de commande pour le test
            test_order.total_amount = amount_xof
            test_order.subtotal = amount_xof
            
            try:
                result = cinetpay_api.initiate_payment(test_order, customer_data)
                
                if result['success']:
                    print(f"  ✅ Transaction créée: {result['transaction_id']}")
                    print(f"  URL: {result['payment_url'][:50]}...")
                    
                    # Tester l'accessibilité immédiate
                    try:
                        url_response = requests.get(result['payment_url'], timeout=10)
                        print(f"  Status URL: {url_response.status_code}")
                        
                        if url_response.status_code == 200:
                            content = url_response.text.lower()
                            if 'error' in content or 'erreur' in content:
                                print("  ⚠️ Erreur détectée sur la page")
                            if 'expired' in content or 'expire' in content:
                                print("  ⚠️ Transaction expirée détectée")
                            else:
                                print("  ✅ Page de paiement OK")
                        else:
                            print(f"  ❌ Page inaccessible: {url_response.status_code}")
                            
                    except Exception as e:
                        print(f"  ❌ Erreur test URL: {e}")
                        
                else:
                    print(f"  ❌ Échec création: {result['error']}")
                    
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
        
        # 2. Analyser les échecs récents
        print("\n2. ANALYSE ECHECS RECENTS")
        print("-" * 40)
        
        failed_transactions = ShopCinetPayTransaction.objects.filter(
            status__in=['failed', 'cancelled']
        ).order_by('-created_at')[:5]
        
        for transaction in failed_transactions:
            print(f"\nTransaction échouée: {transaction.cinetpay_transaction_id}")
            print(f"  Montant: {transaction.amount} {transaction.currency}")
            print(f"  Créée: {transaction.created_at}")
            
            # Vérifier le détail de l'échec
            try:
                verification_data = {
                    'apikey': cinetpay_api.api_key,
                    'site_id': cinetpay_api.site_id,
                    'transaction_id': transaction.cinetpay_transaction_id
                }
                
                verify_response = requests.post(
                    'https://api-checkout.cinetpay.com/v2/payment/check',
                    json=verification_data,
                    timeout=10
                )
                
                if verify_response.status_code == 200:
                    verify_result = verify_response.json()
                    if verify_result.get('data'):
                        data = verify_result['data']
                        print(f"  Raison échec: {data.get('description', 'N/A')}")
                        print(f"  Méthode tentée: {data.get('payment_method', 'N/A')}")
                        print(f"  Opérateur: {data.get('operator_id', 'N/A')}")
                        
                        # Analyser les codes d'erreur spécifiques
                        if data.get('payment_method') == 'VISAM':
                            print("  🔍 Problème avec paiement par carte VISA/Mastercard")
                        
            except Exception as e:
                print(f"  Erreur analyse: {e}")
        
        # 3. Recommandations spécifiques
        print("\n3. RECOMMANDATIONS SPECIFIQUES")
        print("-" * 40)
        
        print("Basé sur l'analyse:")
        print("1. ❌ Problème principal: Paiements VISA/Mastercard échouent")
        print("2. ✅ Mobile Money pourrait mieux fonctionner")
        print("3. 💰 Tester avec des montants plus élevés (>= 1000 XOF)")
        print("4. 🔧 Vérifier la configuration marchande CinetPay")
        print("5. 📞 Contacter CinetPay pour activer les cartes bancaires")
        print("6. 🌍 Vérifier les restrictions géographiques pour VISA")
        
        # 4. Test de création manuelle avec montant élevé
        print("\n4. TEST MONTANT ELEVE MANUEL")
        print("-" * 40)
        
        print("Création d'une transaction 5000 XOF (≈7.5€)...")
        
        # Supprimer les transactions de test
        ShopCinetPayTransaction.objects.filter(order=test_order).delete()
        
        # Test avec montant élevé
        test_order.total_amount = 5000
        test_order.subtotal = 5000
        
        try:
            high_amount_result = cinetpay_api.initiate_payment(test_order, customer_data)
            
            if high_amount_result['success']:
                print("✅ Transaction 5000 XOF créée avec succès!")
                print(f"URL: {high_amount_result['payment_url']}")
                print("\n🎯 RECOMMANDATION URGENTE:")
                print("Teste cette URL manuellement dans un navigateur")
                print("pour voir si le paiement fonctionne avec un montant plus élevé.")
            else:
                print(f"❌ Échec transaction élevée: {high_amount_result['error']}")
                
        except Exception as e:
            print(f"❌ Erreur test montant élevé: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_payment_methods()
