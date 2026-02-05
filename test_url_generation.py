#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.urls import reverse
from django.conf import settings
from blizzgame.models import Order

# Test de génération d'URL
print("=== TEST DE GÉNÉRATION D'URLS ===")
print(f"BASE_URL: {getattr(settings, 'BASE_URL', 'Non défini')}")

# Test avec un UUID valide
test_uuid = "2b5e339e-c0c1-49b5-85d2-65c99bb4c0ea"

try:
    # URL de succès
    success_url = reverse('shop_payment_success', args=[test_uuid])
    print(f"URL de succès: {success_url}")
    
    # URL complète
    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
    full_success_url = f"{base_url}{success_url}"
    print(f"URL complète: {full_success_url}")
    
    # Test avec une commande réelle
    order = Order.objects.first()
    if order:
        print(f"\n=== TEST AVEC COMMANDE RÉELLE ===")
        print(f"Commande ID: {order.id}")
        real_success_url = reverse('shop_payment_success', args=[order.id])
        print(f"URL réelle: {real_success_url}")
        real_full_url = f"{base_url}{real_success_url}"
        print(f"URL complète réelle: {real_full_url}")
    else:
        print("Aucune commande trouvée")
        
except Exception as e:
    print(f"Erreur: {e}")

print("\n=== VÉRIFICATION DES URLS DANS CINETPAY_UTILS ===")
try:
    from blizzgame.cinetpay_utils import CinetPayAPI
    from blizzgame.models import Order
    
    order = Order.objects.first()
    if order:
        api = CinetPayAPI()
        # Simuler la génération d'URL sans faire l'appel API
        from django.urls import reverse
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        return_url = f"{base_url}{reverse('shop_payment_success', args=[order.id])}"
        print(f"URL de retour générée: {return_url}")
    else:
        print("Aucune commande trouvée pour le test")
        
except Exception as e:
    print(f"Erreur dans cinetpay_utils: {e}")
