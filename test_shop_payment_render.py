#!/usr/bin/env python3
"""
Script pour tester le paiement boutique sur Render
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

def test_shop_payment_render():
    """Teste le paiement boutique sur Render"""
    print("TEST PAIEMENT BOUTIQUE SUR RENDER")
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
        
        # 2. Tester la page de paiement (GET)
        print("\n2. TEST PAGE DE PAIEMENT (GET)")
        print("-" * 30)
        
        client = Client()
        payment_url = reverse('initiate_shop_payment', args=[test_order.id])
        print(f"URL de paiement: {payment_url}")
        
        response = client.get(payment_url)
        print(f"Status GET: {response.status_code}")
        
        if response.status_code == 200:
            print("OK: Page de paiement accessible")
        else:
            print("ERREUR: Page de paiement non accessible")
            return False
        
        # 3. Tester la soumission du formulaire (POST AJAX)
        print("\n3. TEST SOUMISSION FORMULAIRE (POST AJAX)")
        print("-" * 30)
        
        # Données de test
        form_data = {
            'customer_name': 'Test',
            'customer_surname': 'User',
            'customer_email': 'test@example.com',
            'customer_phone_country_code': '+221',
            'customer_phone_number': '701234567',
            'customer_address': '123 Test Street',
            'customer_city': 'Dakar',
            'customer_country': 'SN',
            'customer_state': 'Dakar',
            'customer_zip_code': '10000',
        }
        
        print("Donnees de test:")
        for key, value in form_data.items():
            print(f"  {key}: {value}")
        
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
                        transaction = ShopCinetPayTransaction.objects.get(order=test_order)
                        print(f"  Transaction creee: {transaction.cinetpay_transaction_id}")
                        print(f"  Status: {transaction.status}")
                    except ShopCinetPayTransaction.DoesNotExist:
                        print("  PROBLEME: Transaction non creee")
                        
                else:
                    print(f"  Erreur: {response_data.get('error')}")
                    
            except json.JSONDecodeError:
                print("ERREUR: Reponse non-JSON")
                print(f"Contenu: {response.content.decode()[:200]}...")
        else:
            print("ERREUR: Echec POST")
            print(f"Contenu: {response.content.decode()[:200]}...")
        
        # 4. Vérifier les configurations
        print("\n4. VERIFICATION CONFIGURATIONS")
        print("-" * 30)
        
        from django.conf import settings
        
        configs = [
            ('CINETPAY_API_KEY', getattr(settings, 'CINETPAY_API_KEY', None)),
            ('CINETPAY_SITE_ID', getattr(settings, 'CINETPAY_SITE_ID', None)),
            ('BASE_URL', getattr(settings, 'BASE_URL', None)),
            ('ENVIRONMENT', os.environ.get('ENVIRONMENT', 'development')),
        ]
        
        for name, value in configs:
            if value:
                if 'KEY' in name:
                    print(f"  {name}: {'*' * 20}...{str(value)[-4:]}")
                else:
                    print(f"  {name}: {value}")
            else:
                print(f"  {name}: NON CONFIGURE")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_shop_payment_render()
