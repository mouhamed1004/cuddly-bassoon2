#!/usr/bin/env python3
"""
Script de diagnostic avancé pour identifier les échecs de paiement
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order, ShopCinetPayTransaction
from blizzgame.cinetpay_utils import CinetPayAPI
from django.test import Client
from django.urls import reverse
import json
import logging

# Configuration du logging pour voir les erreurs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_payment_failure():
    """Diagnostic avancé des échecs de paiement"""
    print("DIAGNOSTIC AVANCE DES ECHECS DE PAIEMENT")
    print("=" * 60)
    
    try:
        # 1. Vérifier l'état actuel
        print("\n1. ETAT ACTUEL DU SYSTEME")
        print("-" * 40)
        
        pending_orders = Order.objects.filter(payment_status='pending').order_by('-created_at')
        failed_orders = Order.objects.filter(payment_status='failed').order_by('-created_at')
        paid_orders = Order.objects.filter(payment_status='paid').order_by('-created_at')
        
        print(f"Commandes en attente: {pending_orders.count()}")
        print(f"Commandes echouees: {failed_orders.count()}")
        print(f"Commandes payees: {paid_orders.count()}")
        
        # Transactions CinetPay
        all_transactions = ShopCinetPayTransaction.objects.all().order_by('-created_at')
        pending_transactions = all_transactions.filter(status='pending')
        completed_transactions = all_transactions.filter(status='completed')
        failed_transactions = all_transactions.filter(status='failed')
        
        print(f"Transactions CinetPay totales: {all_transactions.count()}")
        print(f"  - En attente: {pending_transactions.count()}")
        print(f"  - Completees: {completed_transactions.count()}")
        print(f"  - Echouees: {failed_transactions.count()}")
        
        # 2. Analyser la dernière tentative
        print("\n2. ANALYSE DE LA DERNIERE TENTATIVE")
        print("-" * 40)
        
        if pending_orders.exists():
            latest_order = pending_orders.first()
            print(f"Derniere commande: #{latest_order.order_number}")
            print(f"Montant: {latest_order.total_amount}")
            print(f"Email: {latest_order.customer_email}")
            print(f"Cree le: {latest_order.created_at}")
            
            # Vérifier si une transaction CinetPay existe
            try:
                cinetpay_transaction = ShopCinetPayTransaction.objects.get(order=latest_order)
                print(f"Transaction CinetPay trouvee:")
                print(f"  ID: {cinetpay_transaction.cinetpay_transaction_id}")
                print(f"  Status: {cinetpay_transaction.status}")
                print(f"  URL: {cinetpay_transaction.payment_url}")
                print(f"  Customer name: '{cinetpay_transaction.customer_name}'")
                print(f"  Customer surname: '{cinetpay_transaction.customer_surname}'")
                print(f"  Customer phone: '{cinetpay_transaction.customer_phone_number}'")
                print(f"  Customer email: '{cinetpay_transaction.customer_email}'")
            except ShopCinetPayTransaction.DoesNotExist:
                print("PROBLEME: Aucune transaction CinetPay pour cette commande")
            except ShopCinetPayTransaction.MultipleObjectsReturned:
                transactions = ShopCinetPayTransaction.objects.filter(order=latest_order)
                print(f"ATTENTION: {transactions.count()} transactions pour cette commande")
                for i, trans in enumerate(transactions):
                    print(f"  Transaction {i+1}: {trans.cinetpay_transaction_id} - {trans.status}")
        
        # 3. Test de création de paiement en direct
        print("\n3. TEST CREATION PAIEMENT EN DIRECT")
        print("-" * 40)
        
        if pending_orders.exists():
            test_order = pending_orders.first()
            
            # Données client de test
            customer_data = {
                'customer_name': 'TestUser',
                'customer_surname': 'Diagnostic',
                'customer_email': 'diagnostic@blizz.com',
                'customer_phone_number': '+221701234567',
                'customer_address': '123 Test Street',
                'customer_city': 'Dakar',
                'customer_country': 'SN',
                'customer_state': 'Dakar',
                'customer_zip_code': '10000',
            }
            
            print("Test direct avec API CinetPay...")
            print(f"Commande test: #{test_order.order_number}")
            print(f"Montant: {test_order.total_amount}")
            
            try:
                # Tester l'API CinetPay directement
                cinetpay_api = CinetPayAPI()
                
                # Convertir le montant
                from blizzgame.currency_service import CurrencyService
                converted_amount = CurrencyService.convert_amount(test_order.total_amount, 'EUR', 'XOF')
                print(f"Montant converti: {converted_amount} XOF")
                
                # Créer une copie de la commande pour le test
                test_order.total_amount = converted_amount
                test_order.subtotal = converted_amount
                
                # Supprimer les transactions existantes pour ce test
                ShopCinetPayTransaction.objects.filter(order=test_order).delete()
                print("Transactions existantes supprimees pour le test")
                
                # Tester l'initiation
                result = cinetpay_api.initiate_payment(test_order, customer_data)
                
                if result['success']:
                    print("SUCCESS: Paiement initie avec succes!")
                    print(f"Transaction ID: {result['transaction_id']}")
                    print(f"Payment URL: {result['payment_url'][:100]}...")
                    
                    # Vérifier la transaction créée
                    new_transaction = ShopCinetPayTransaction.objects.get(order=test_order)
                    print(f"Transaction creee avec:")
                    print(f"  customer_name: '{new_transaction.customer_name}'")
                    print(f"  customer_surname: '{new_transaction.customer_surname}'")
                    print(f"  customer_phone: '{new_transaction.customer_phone_number}'")
                    
                else:
                    print(f"ECHEC: {result['error']}")
                    
            except Exception as e:
                print(f"ERREUR lors du test direct: {e}")
                import traceback
                traceback.print_exc()
        
        # 4. Test du formulaire web
        print("\n4. TEST FORMULAIRE WEB")
        print("-" * 40)
        
        if pending_orders.count() > 1:
            test_order_web = pending_orders[1]
            
            client = Client()
            payment_url = reverse('initiate_shop_payment', args=[test_order_web.id])
            
            # Test GET
            response_get = client.get(payment_url)
            print(f"GET {payment_url}: {response_get.status_code}")
            
            # Test POST
            form_data = {
                'customer_name': 'WebTest',
                'customer_surname': 'User',
                'customer_email': 'webtest@blizz.com',
                'customer_phone_country_code': '+221',
                'customer_phone_number': '701234567',
                'customer_address': '123 Web Street',
                'customer_city': 'Dakar',
                'customer_country': 'SN',
                'customer_state': 'Dakar',
                'customer_zip_code': '10000',
            }
            
            # Supprimer les transactions existantes
            ShopCinetPayTransaction.objects.filter(order=test_order_web).delete()
            
            response_post = client.post(
                payment_url,
                data=form_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                HTTP_ACCEPT='application/json',
                content_type='application/x-www-form-urlencoded'
            )
            
            print(f"POST {payment_url}: {response_post.status_code}")
            
            if response_post.status_code == 200:
                try:
                    response_data = json.loads(response_post.content)
                    print(f"Reponse JSON: success={response_data.get('success')}")
                    if not response_data.get('success'):
                        print(f"Erreur: {response_data.get('error')}")
                except json.JSONDecodeError:
                    print("Reponse non-JSON:")
                    print(response_post.content.decode()[:500])
        
        # 5. Vérifier les configurations
        print("\n5. VERIFICATION CONFIGURATIONS")
        print("-" * 40)
        
        from django.conf import settings
        
        api_key = getattr(settings, 'CINETPAY_API_KEY', None)
        site_id = getattr(settings, 'CINETPAY_SITE_ID', None)
        base_url = getattr(settings, 'BASE_URL', None)
        
        print(f"CINETPAY_API_KEY: {'OK' if api_key else 'MANQUANT'}")
        print(f"CINETPAY_SITE_ID: {site_id if site_id else 'MANQUANT'}")
        print(f"BASE_URL: {base_url if base_url else 'MANQUANT'}")
        print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT', 'development')}")
        
        # Test de connectivité CinetPay
        print("\n6. TEST CONNECTIVITE CINETPAY")
        print("-" * 40)
        
        try:
            import requests
            test_url = "https://api-checkout.cinetpay.com/v2/payment"
            test_response = requests.get(test_url, timeout=10)
            print(f"Connectivite CinetPay: {test_response.status_code}")
        except Exception as e:
            print(f"Probleme connectivite CinetPay: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR generale: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    diagnose_payment_failure()
