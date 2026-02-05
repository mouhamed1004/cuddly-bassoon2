#!/usr/bin/env python3
"""
Script pour diagnostiquer et corriger le problème de formatage des données du formulaire
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order
from django.test import Client
from django.urls import reverse
import json

def fix_form_data_issue():
    """Diagnostique et corrige le problème de formatage des données du formulaire"""
    print("DIAGNOSTIC PROBLEME FORMATAGE DONNEES FORMULAIRE")
    print("=" * 60)
    
    try:
        # 1. Tester différents formats de données
        print("\n1. TEST DIFFERENTS FORMATS DE DONNEES")
        print("-" * 40)
        
        pending_orders = Order.objects.filter(payment_status='pending').order_by('-created_at')
        if not pending_orders.exists():
            print("Aucune commande en attente pour tester")
            return False
        
        test_order = pending_orders.first()
        client = Client()
        payment_url = reverse('initiate_shop_payment', args=[test_order.id])
        
        # Test 1: Données normales (comme un vrai formulaire)
        print("\nTest 1: Donnees normales")
        form_data_normal = {
            'customer_name': 'TestNormal',
            'customer_surname': 'User',
            'customer_email': 'normal@test.com',
            'customer_phone_country_code': '+221',
            'customer_phone_number': '701234567',
            'customer_address': '123 Normal Street',
            'customer_city': 'Dakar',
            'customer_country': 'SN',
            'customer_state': 'Dakar',
            'customer_zip_code': '10000',
        }
        
        response1 = client.post(
            payment_url,
            data=form_data_normal,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            content_type='application/x-www-form-urlencoded'
        )
        
        print(f"Status: {response1.status_code}")
        if response1.status_code == 200:
            try:
                data1 = json.loads(response1.content)
                print(f"Success: {data1.get('success')}")
                if not data1.get('success'):
                    print(f"Erreur: {data1.get('error')}")
            except:
                print("Reponse non-JSON")
        
        # Test 2: Données avec Content-Type multipart/form-data
        print("\nTest 2: Donnees multipart/form-data")
        from django.test import RequestFactory
        from django.http import QueryDict
        from blizzgame.views import shop_payment
        
        factory = RequestFactory()
        
        # Simuler une vraie requête multipart
        post_data = QueryDict('', mutable=True)
        post_data.update(form_data_normal)
        
        request = factory.post(
            payment_url,
            data=post_data,
            content_type='multipart/form-data'
        )
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        
        try:
            response2 = shop_payment(request, test_order.id)
            print(f"Status: {response2.status_code}")
            if hasattr(response2, 'content'):
                try:
                    data2 = json.loads(response2.content)
                    print(f"Success: {data2.get('success')}")
                    if not data2.get('success'):
                        print(f"Erreur: {data2.get('error')}")
                except:
                    print("Reponse non-JSON")
        except Exception as e:
            print(f"Erreur: {e}")
        
        # Test 3: Analyser les logs Django pour comprendre le formatage
        print("\n2. ANALYSE DU PROBLEME DE FORMATAGE")
        print("-" * 40)
        
        print("Le probleme identifie:")
        print("- Les donnees POST arrivent comme: {\"{'customer_name': 'WebTest', ...}\": ['']}")
        print("- Au lieu de: {'customer_name': 'WebTest', 'customer_surname': 'User', ...}")
        print("")
        print("Cela indique que le JavaScript envoie les donnees dans un format incorrect.")
        print("Le FormData n'est pas correctement serialise.")
        
        # Test 4: Vérifier si c'est un problème de CSRF
        print("\n3. TEST CSRF ET HEADERS")
        print("-" * 40)
        
        # Obtenir le token CSRF
        csrf_response = client.get(payment_url)
        csrf_token = csrf_response.context['csrf_token'] if csrf_response.context else None
        
        if csrf_token:
            print(f"CSRF Token obtenu: {str(csrf_token)[:20]}...")
            
            # Test avec CSRF correct
            form_data_csrf = form_data_normal.copy()
            form_data_csrf['csrfmiddlewaretoken'] = str(csrf_token)
            
            response3 = client.post(
                payment_url,
                data=form_data_csrf,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                HTTP_ACCEPT='application/json'
            )
            
            print(f"Status avec CSRF: {response3.status_code}")
            if response3.status_code == 200:
                try:
                    data3 = json.loads(response3.content)
                    print(f"Success avec CSRF: {data3.get('success')}")
                    if not data3.get('success'):
                        print(f"Erreur avec CSRF: {data3.get('error')}")
                except:
                    print("Reponse non-JSON avec CSRF")
        
        print("\n4. RECOMMANDATIONS")
        print("-" * 40)
        print("1. Le probleme principal est dans le JavaScript du formulaire")
        print("2. Les donnees sont mal formatees lors de l'envoi AJAX")
        print("3. Il faut corriger le JavaScript pour envoyer les donnees correctement")
        print("4. Verifier que le CSRF token est correctement inclus")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_form_data_issue()
