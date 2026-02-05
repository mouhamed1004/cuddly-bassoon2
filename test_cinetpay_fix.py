#!/usr/bin/env python3
"""
Script pour tester la correction du problème CinetPay
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

def test_cinetpay_fix():
    """Teste la correction du problème CinetPay"""
    print("TEST CORRECTION PROBLEME CINETPAY")
    print("=" * 50)
    
    try:
        # 1. Vérifier les commandes en attente
        print("\n1. COMMANDES EN ATTENTE")
        print("-" * 30)
        
        pending_orders = Order.objects.filter(payment_status='pending').order_by('-created_at')
        print(f"Commandes en attente: {pending_orders.count()}")
        
        if pending_orders.count() == 0:
            print("Aucune commande pour tester")
            return False
        
        test_order = pending_orders.first()
        print(f"Test avec: #{test_order.order_number}")
        print(f"Montant: {test_order.total_amount}")
        
        # Vérifier les données client de la commande
        print(f"Customer first name: '{test_order.customer_first_name}'")
        print(f"Customer last name: '{test_order.customer_last_name}'")
        print(f"Customer phone: '{test_order.customer_phone}'")
        print(f"Customer email: '{test_order.customer_email}'")
        
        # 2. Tester la soumission avec la correction
        print("\n2. TEST SOUMISSION AVEC CORRECTION")
        print("-" * 30)
        
        client = Client()
        payment_url = reverse('initiate_shop_payment', args=[test_order.id])
        
        # Données de test avec des valeurs vides pour tester le fallback
        form_data = {
            'customer_name': '',  # Vide pour tester le fallback
            'customer_surname': '',  # Vide pour tester le fallback
            'customer_email': 'test@example.com',
            'customer_phone_country_code': '+221',
            'customer_phone_number': '701234567',
            'customer_address': '123 Test Street',
            'customer_city': 'Dakar',
            'customer_country': 'SN',
            'customer_state': 'Dakar',
            'customer_zip_code': '10000',
        }
        
        print("Donnees de test (avec champs vides):")
        for key, value in form_data.items():
            print(f"  {key}: '{value}'")
        
        # Simuler une requête AJAX POST
        response = client.post(
            payment_url,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
            content_type='application/x-www-form-urlencoded'
        )
        
        print(f"Status POST: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_data = json.loads(response.content)
                print("Reponse JSON:")
                print(f"  Success: {response_data.get('success')}")
                
                if response_data.get('success'):
                    print(f"  Redirect URL: {response_data.get('redirect_url')}")
                    print("SUCCESS: Paiement initie avec succes!")
                    
                    # Vérifier transaction créée
                    try:
                        transaction = ShopCinetPayTransaction.objects.filter(order=test_order).last()
                        if transaction:
                            print(f"  Transaction creee: {transaction.cinetpay_transaction_id}")
                            print(f"  Status: {transaction.status}")
                            print(f"  Customer name: '{transaction.customer_name}'")
                            print(f"  Customer surname: '{transaction.customer_surname}'")
                            print(f"  Customer phone: '{transaction.customer_phone_number}'")
                            print(f"  Customer email: '{transaction.customer_email}'")
                            print(f"  Customer country: '{transaction.customer_country}'")
                            
                            # Vérifier que les valeurs par défaut ont été utilisées
                            if transaction.customer_name in ['Client', test_order.customer_first_name]:
                                print("  OK: Fallback customer_name fonctionne")
                            else:
                                print(f"  PROBLEME: customer_name = '{transaction.customer_name}'")
                                
                        else:
                            print("  PROBLEME: Transaction non trouvee")
                    except Exception as e:
                        print(f"  ERREUR verification transaction: {e}")
                        
                else:
                    print(f"  Erreur: {response_data.get('error')}")
                    return False
                    
            except json.JSONDecodeError:
                print("ERREUR: Reponse non-JSON")
                print(f"Contenu: {response.content.decode()[:200]}...")
                return False
        else:
            print("ERREUR: Echec POST")
            print(f"Contenu: {response.content.decode()[:200]}...")
            return False
        
        # 3. Test avec données complètes
        print("\n3. TEST AVEC DONNEES COMPLETES")
        print("-" * 30)
        
        form_data_complete = {
            'customer_name': 'Jean',
            'customer_surname': 'Dupont',
            'customer_email': 'jean.dupont@example.com',
            'customer_phone_country_code': '+221',
            'customer_phone_number': '701234567',
            'customer_address': '456 Complete Street',
            'customer_city': 'Dakar',
            'customer_country': 'SN',
            'customer_state': 'Dakar',
            'customer_zip_code': '10000',
        }
        
        # Prendre une autre commande ou créer une nouvelle pour ce test
        test_order2 = pending_orders[1] if pending_orders.count() > 1 else test_order
        payment_url2 = reverse('initiate_shop_payment', args=[test_order2.id])
        
        response2 = client.post(
            payment_url2,
            data=form_data_complete,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
            content_type='application/x-www-form-urlencoded'
        )
        
        if response2.status_code == 200:
            try:
                response_data2 = json.loads(response2.content)
                if response_data2.get('success'):
                    print("SUCCESS: Test avec donnees completes reussi!")
                    
                    # Vérifier transaction
                    transaction2 = ShopCinetPayTransaction.objects.filter(order=test_order2).last()
                    if transaction2:
                        print(f"  Customer name: '{transaction2.customer_name}'")
                        print(f"  Customer surname: '{transaction2.customer_surname}'")
                        
                        if transaction2.customer_name == 'Jean' and transaction2.customer_surname == 'Dupont':
                            print("  OK: Donnees completes correctement utilisees")
                        else:
                            print("  PROBLEME: Donnees non utilisees correctement")
                else:
                    print(f"  Erreur: {response_data2.get('error')}")
            except json.JSONDecodeError:
                print("ERREUR: Reponse non-JSON pour test complet")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_cinetpay_fix()
