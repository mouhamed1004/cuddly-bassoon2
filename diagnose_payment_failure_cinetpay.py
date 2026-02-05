#!/usr/bin/env python3
"""
Script pour diagnostiquer les échecs de paiement sur CinetPay
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import ShopCinetPayTransaction
from blizzgame.cinetpay_utils import CinetPayAPI
from django.conf import settings
import requests

def diagnose_payment_failure_cinetpay():
    """Diagnostique les échecs de paiement sur CinetPay"""
    print("DIAGNOSTIC ECHECS PAIEMENT CINETPAY")
    print("=" * 50)
    
    try:
        # 1. Vérifier la configuration CinetPay
        print("\n1. CONFIGURATION CINETPAY")
        print("-" * 30)
        
        api_key = settings.CINETPAY_API_KEY
        site_id = settings.CINETPAY_SITE_ID
        
        print(f"API Key: {'*' * 20}...{api_key[-4:]}")
        print(f"Site ID: {site_id}")
        
        # 2. Tester la connexion API
        print("\n2. TEST CONNEXION API CINETPAY")
        print("-" * 30)
        
        try:
            test_data = {
                'apikey': api_key,
                'site_id': site_id
            }
            
            # Test endpoint de vérification
            response = requests.post(
                'https://api-checkout.cinetpay.com/v2/payment/check',
                json=test_data,
                timeout=10
            )
            
            print(f"Status API: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Code response: {result.get('code')}")
                print(f"Message: {result.get('message')}")
            else:
                print(f"Erreur HTTP: {response.text[:200]}")
                
        except Exception as e:
            print(f"Erreur test API: {e}")
        
        # 3. Analyser les transactions récentes
        print("\n3. ANALYSE TRANSACTIONS RECENTES")
        print("-" * 30)
        
        recent_transactions = ShopCinetPayTransaction.objects.all().order_by('-created_at')[:5]
        
        for transaction in recent_transactions:
            print(f"\nTransaction: {transaction.cinetpay_transaction_id}")
            print(f"  Montant: {transaction.amount} {transaction.currency}")
            print(f"  Status: {transaction.status}")
            print(f"  Créée: {transaction.created_at}")
            
            # Vérifier le statut détaillé
            try:
                cinetpay_api = CinetPayAPI()
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
                    print(f"  Code CinetPay: {verify_result.get('code')}")
                    print(f"  Message CinetPay: {verify_result.get('message')}")
                    
                    if verify_result.get('data'):
                        data = verify_result['data']
                        print(f"  Status paiement: {data.get('status')}")
                        print(f"  Description: {data.get('description', 'N/A')}")
                        
                        # Informations détaillées si disponibles
                        if 'operator_id' in data:
                            print(f"  Opérateur: {data.get('operator_id')}")
                        if 'payment_method' in data:
                            print(f"  Méthode: {data.get('payment_method')}")
                            
                else:
                    print(f"  Erreur vérification: {verify_response.status_code}")
                    
            except Exception as e:
                print(f"  Erreur détail: {e}")
        
        # 4. Vérifier les limites et restrictions
        print("\n4. VERIFICATION LIMITES ET RESTRICTIONS")
        print("-" * 30)
        
        # Montants testés
        test_amounts = [105, 500, 1000, 5000]  # En XOF
        
        for amount in test_amounts:
            print(f"\nTest montant: {amount} XOF")
            
            # Vérifier si le montant est valide
            from blizzgame.cinetpay_utils import validate_cinetpay_amount
            is_valid, message = validate_cinetpay_amount(amount, 'XOF')
            
            print(f"  Validation: {is_valid}")
            if not is_valid:
                print(f"  Erreur: {message}")
        
        # 5. Tester la création d'une micro-transaction
        print("\n5. TEST MICRO-TRANSACTION")
        print("-" * 30)
        
        print("Création d'une transaction de test avec montant plus élevé...")
        
        # Créer une transaction de test avec 1000 XOF (environ 1.5€)
        test_transaction_id = f"TEST_DIAG_{os.urandom(4).hex()}"
        
        test_payment_data = {
            'apikey': api_key,
            'site_id': site_id,
            'transaction_id': test_transaction_id,
            'amount': 1000,  # 1000 XOF = ~1.5€
            'currency': 'XOF',
            'description': 'Test diagnostic paiement',
            'customer_name': 'Test',
            'customer_surname': 'Diagnostic',
            'customer_email': 'test@diagnostic.com',
            'customer_phone_number': '+221701234567',
            'customer_address': 'Test Address',
            'customer_city': 'Dakar',
            'customer_country': 'SN',
            'customer_state': 'Dakar',
            'customer_zip_code': '10000',
            'return_url': f"{settings.BASE_URL}/test/success/",
            'notify_url': f"{settings.BASE_URL}/test/notify/",
            'cancel_url': f"{settings.BASE_URL}/test/cancel/"
        }
        
        try:
            test_response = requests.post(
                'https://api-checkout.cinetpay.com/v2/payment',
                json=test_payment_data,
                timeout=30
            )
            
            print(f"Status création test: {test_response.status_code}")
            
            if test_response.status_code == 200:
                test_result = test_response.json()
                print(f"Code: {test_result.get('code')}")
                print(f"Message: {test_result.get('message')}")
                
                if test_result.get('code') == '201':
                    payment_url = test_result['data']['payment_url']
                    print(f"✅ Transaction test créée!")
                    print(f"URL test: {payment_url[:50]}...")
                    
                    # Tester l'accessibilité
                    try:
                        url_response = requests.get(payment_url, timeout=10)
                        print(f"URL accessible: {url_response.status_code}")
                    except Exception as e:
                        print(f"Erreur URL test: {e}")
                        
                else:
                    print(f"❌ Échec création: {test_result.get('message')}")
            else:
                print(f"❌ Erreur HTTP: {test_response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Erreur test création: {e}")
        
        # 6. Recommandations
        print("\n6. RECOMMANDATIONS")
        print("-" * 30)
        print("1. Vérifier que le compte CinetPay est activé pour la production")
        print("2. Confirmer que les méthodes de paiement sont activées")
        print("3. Vérifier les limites de montant minimum/maximum")
        print("4. Tester avec différents montants")
        print("5. Contacter le support CinetPay si nécessaire")
        print("6. Vérifier les restrictions géographiques")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    diagnose_payment_failure_cinetpay()
