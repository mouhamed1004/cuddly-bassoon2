#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order
from blizzgame.cinetpay_utils import CinetPayAPI

# Test du flux de paiement
print("=== TEST DU FLUX DE PAIEMENT ===")

try:
    # Récupérer une commande
    order = Order.objects.first()
    if not order:
        print("Aucune commande trouvée")
        sys.exit(1)
    
    print(f"Commande trouvée: {order.id}")
    print(f"Montant: {order.total_amount}")
    
    # Données client de test
    customer_data = {
        'customer_name': 'Test',
        'customer_surname': 'User',
        'customer_email': 'test@example.com',
        'customer_phone_number': '+225123456789',
        'customer_address': 'Test Address',
        'customer_city': 'Abidjan',
        'customer_country': 'CI',
        'customer_state': 'Abidjan',
        'customer_zip_code': '12345',
    }
    
    # Initialiser l'API CinetPay
    api = CinetPayAPI()
    print(f"Mode test CinetPay: {api.test_mode}")
    
    # Tester l'initiation du paiement
    print("\n=== INITIATION DU PAIEMENT ===")
    result = api.initiate_payment(order, customer_data)
    
    print(f"Succès: {result['success']}")
    if result['success']:
        print(f"URL de paiement: {result['payment_url']}")
        print(f"ID de transaction: {result['transaction_id']}")
    else:
        print(f"Erreur: {result['error']}")
        
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
