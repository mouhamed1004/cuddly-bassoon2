#!/usr/bin/env python3
"""
Script pour tester le flux de paiement boutique et identifier les blocages
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order, Product, OrderItem, ShopCinetPayTransaction
from blizzgame.cinetpay_utils import CinetPayAPI, validate_cinetpay_amount
from blizzgame.currency_service import CurrencyService
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def test_shop_payment_flow():
    """Teste le flux de paiement boutique"""
    print("TEST DU FLUX DE PAIEMENT BOUTIQUE")
    print("=" * 50)
    
    try:
        # 1. Vérifier qu'il y a des commandes en attente
        print("\n1. VERIFICATION DES COMMANDES EN ATTENTE")
        print("-" * 40)
        
        pending_orders = Order.objects.filter(payment_status='pending').order_by('-created_at')
        print(f"Commandes en attente: {pending_orders.count()}")
        
        if pending_orders.count() == 0:
            print("Aucune commande en attente pour tester")
            return False
        
        # Prendre la première commande en attente
        test_order = pending_orders.first()
        print(f"Test avec commande: #{test_order.order_number}")
        print(f"Montant: {test_order.total_amount}€")
        
        # 2. Tester la conversion de devise
        print("\n2. TEST CONVERSION DE DEVISE")
        print("-" * 40)
        
        original_amount = test_order.total_amount
        print(f"Montant original: {original_amount} EUR")
        
        try:
            converted_amount = CurrencyService.convert_amount(original_amount, 'EUR', 'XOF')
            print(f"Montant converti: {converted_amount} XOF")
        except Exception as e:
            print(f"ERREUR conversion: {e}")
            return False
        
        # 3. Tester la validation du montant CinetPay
        print("\n3. TEST VALIDATION MONTANT CINETPAY")
        print("-" * 40)
        
        try:
            is_valid, message = validate_cinetpay_amount(converted_amount, 'XOF')
            print(f"Validation: {is_valid}")
            if not is_valid:
                print(f"Message d'erreur: {message}")
                return False
            else:
                print("Montant valide pour CinetPay")
        except Exception as e:
            print(f"ERREUR validation: {e}")
            return False
        
        # 4. Tester l'initialisation de l'API CinetPay
        print("\n4. TEST INITIALISATION API CINETPAY")
        print("-" * 40)
        
        try:
            cinetpay_api = CinetPayAPI()
            print("API CinetPay initialisée avec succès")
            print(f"API Key: {'*' * 20}...{cinetpay_api.api_key[-4:]}")
            print(f"Site ID: {cinetpay_api.site_id}")
        except Exception as e:
            print(f"ERREUR initialisation API: {e}")
            return False
        
        # 5. Tester l'initiation de paiement (simulation)
        print("\n5. TEST INITIATION DE PAIEMENT (SIMULATION)")
        print("-" * 40)
        
        # Données client fictives
        customer_data = {
            'customer_name': 'Test',
            'customer_surname': 'User',
            'customer_email': 'test@example.com',
            'customer_phone_number': '+221701234567',
            'customer_address': '123 Test Street',
            'customer_city': 'Dakar',
            'customer_country': 'SN',
            'customer_state': 'Dakar',
            'customer_zip_code': '10000',
        }
        
        print("Données client de test:")
        for key, value in customer_data.items():
            print(f"  {key}: {value}")
        
        # Créer une copie de la commande pour le test
        test_order_copy = Order.objects.get(id=test_order.id)
        test_order_copy.total_amount = converted_amount
        test_order_copy.subtotal = converted_amount
        
        try:
            # Tester l'initiation de paiement
            print("\nInitiation du paiement CinetPay...")
            result = cinetpay_api.initiate_payment(test_order_copy, customer_data)
            
            if result['success']:
                print("SUCCESS: Paiement initié avec succès!")
                print(f"Transaction ID: {result['transaction_id']}")
                print(f"Payment URL: {result['payment_url']}")
                
                # Vérifier que la transaction a été créée
                try:
                    shop_transaction = ShopCinetPayTransaction.objects.get(order=test_order_copy)
                    print(f"Transaction CinetPay créée: {shop_transaction.cinetpay_transaction_id}")
                    print(f"Status: {shop_transaction.status}")
                except ShopCinetPayTransaction.DoesNotExist:
                    print("ERREUR: Transaction CinetPay non créée dans la base")
                
            else:
                print(f"ERREUR: Échec de l'initiation de paiement")
                print(f"Erreur: {result['error']}")
                return False
                
        except Exception as e:
            print(f"ERREUR lors de l'initiation: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 6. Vérifier les logs et les problèmes potentiels
        print("\n6. VERIFICATION DES PROBLEMES POTENTIELS")
        print("-" * 40)
        
        # Vérifier les configurations
        from django.conf import settings
        
        if hasattr(settings, 'CINETPAY_API_KEY') and settings.CINETPAY_API_KEY:
            print("OK: CINETPAY_API_KEY configurée")
        else:
            print("ERREUR: CINETPAY_API_KEY non configurée")
        
        if hasattr(settings, 'CINETPAY_SITE_ID') and settings.CINETPAY_SITE_ID:
            print("OK: CINETPAY_SITE_ID configurée")
        else:
            print("ERREUR: CINETPAY_SITE_ID non configurée")
        
        if hasattr(settings, 'BASE_URL') and settings.BASE_URL:
            print(f"OK: BASE_URL configurée: {settings.BASE_URL}")
        else:
            print("ERREUR: BASE_URL non configurée")
        
        return True
        
    except Exception as e:
        print(f"ERREUR générale: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_shop_payment_flow()
