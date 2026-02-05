#!/usr/bin/env python3
"""
Script pour tester l'expérience utilisateur sur les URLs de paiement CinetPay
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order, ShopCinetPayTransaction
import requests
from urllib.parse import urlparse

def test_user_experience():
    """Teste l'expérience utilisateur sur les URLs de paiement"""
    print("TEST EXPERIENCE UTILISATEUR URLS PAIEMENT")
    print("=" * 50)
    
    try:
        # 1. Récupérer les URLs de paiement en attente
        print("\n1. URLS DE PAIEMENT EN ATTENTE")
        print("-" * 40)
        
        pending_transactions = ShopCinetPayTransaction.objects.filter(status='pending')
        
        for transaction in pending_transactions:
            print(f"\nTransaction: {transaction.cinetpay_transaction_id}")
            print(f"Commande: #{transaction.order.order_number}")
            print(f"URL de paiement: {transaction.payment_url}")
            
            # Tester l'accessibilité de l'URL
            try:
                response = requests.get(transaction.payment_url, timeout=15)
                print(f"Status HTTP: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ URL accessible")
                    
                    # Analyser le contenu
                    content = response.text.lower()
                    
                    # Vérifications de base
                    if 'cinetpay' in content:
                        print("✅ Page CinetPay détectée")
                    
                    if 'error' in content or 'erreur' in content:
                        print("⚠️ Erreur détectée dans la page")
                    
                    if 'expired' in content or 'expire' in content:
                        print("⚠️ Transaction expirée détectée")
                    
                    if 'amount' in content or 'montant' in content:
                        print("✅ Montant affiché")
                    
                    # Vérifier la taille de la réponse
                    content_length = len(response.content)
                    print(f"Taille du contenu: {content_length} bytes")
                    
                    if content_length < 1000:
                        print("⚠️ Contenu très petit - possible erreur")
                        print(f"Contenu: {response.text[:500]}")
                    
                elif response.status_code == 404:
                    print("❌ URL non trouvée (404)")
                elif response.status_code == 500:
                    print("❌ Erreur serveur CinetPay (500)")
                else:
                    print(f"⚠️ Status inhabituel: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print("❌ Timeout - URL trop lente")
            except requests.exceptions.ConnectionError:
                print("❌ Erreur de connexion")
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        # 2. Tester la création d'une nouvelle URL
        print("\n2. TEST CREATION NOUVELLE URL")
        print("-" * 40)
        
        # Prendre une commande en attente pour tester
        pending_orders = Order.objects.filter(payment_status='pending')
        if pending_orders.exists():
            test_order = pending_orders.first()
            
            print(f"Test avec commande: #{test_order.order_number}")
            print(f"Montant: {test_order.total_amount}")
            
            # Créer une nouvelle transaction de test
            from blizzgame.cinetpay_utils import CinetPayAPI
            from blizzgame.currency_service import CurrencyService
            
            # Supprimer les anciennes transactions pour ce test
            ShopCinetPayTransaction.objects.filter(order=test_order).delete()
            
            customer_data = {
                'customer_name': 'TestUX',
                'customer_surname': 'Experience',
                'customer_email': 'ux@test.com',
                'customer_phone_number': '+221701234567',
                'customer_address': '123 UX Street',
                'customer_city': 'Dakar',
                'customer_country': 'SN',
                'customer_state': 'Dakar',
                'customer_zip_code': '10000',
            }
            
            # Convertir le montant
            converted_amount = CurrencyService.convert_amount(test_order.total_amount, 'EUR', 'XOF')
            test_order.total_amount = converted_amount
            test_order.subtotal = converted_amount
            
            try:
                cinetpay_api = CinetPayAPI()
                result = cinetpay_api.initiate_payment(test_order, customer_data)
                
                if result['success']:
                    print("✅ Nouvelle URL créée avec succès")
                    new_url = result['payment_url']
                    print(f"Nouvelle URL: {new_url}")
                    
                    # Tester immédiatement la nouvelle URL
                    try:
                        new_response = requests.get(new_url, timeout=15)
                        print(f"Nouvelle URL status: {new_response.status_code}")
                        
                        if new_response.status_code == 200:
                            print("✅ Nouvelle URL accessible immédiatement")
                        else:
                            print(f"⚠️ Problème avec nouvelle URL: {new_response.status_code}")
                            
                    except Exception as e:
                        print(f"❌ Erreur test nouvelle URL: {e}")
                        
                else:
                    print(f"❌ Échec création nouvelle URL: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Erreur création test: {e}")
        
        # 3. Analyser les patterns d'abandon
        print("\n3. ANALYSE PATTERNS D'ABANDON")
        print("-" * 40)
        
        total_transactions = ShopCinetPayTransaction.objects.count()
        pending_count = ShopCinetPayTransaction.objects.filter(status='pending').count()
        completed_count = ShopCinetPayTransaction.objects.filter(status='completed').count()
        
        if total_transactions > 0:
            abandon_rate = (pending_count / total_transactions) * 100
            completion_rate = (completed_count / total_transactions) * 100
            
            print(f"Total transactions: {total_transactions}")
            print(f"En attente (abandonnées): {pending_count} ({abandon_rate:.1f}%)")
            print(f"Complétées: {completed_count} ({completion_rate:.1f}%)")
            
            if abandon_rate > 50:
                print("🚨 TAUX D'ABANDON TRÈS ÉLEVÉ!")
                print("Causes possibles:")
                print("- URLs de paiement non fonctionnelles")
                print("- Interface CinetPay confuse")
                print("- Problème de confiance utilisateur")
                print("- Montants incorrects affichés")
                print("- Processus trop complexe")
        
        # 4. Recommandations
        print("\n4. RECOMMANDATIONS")
        print("-" * 40)
        print("1. Tester manuellement les URLs de paiement dans un navigateur")
        print("2. Vérifier l'interface utilisateur CinetPay")
        print("3. Simplifier le processus de paiement si possible")
        print("4. Ajouter des instructions claires pour les utilisateurs")
        print("5. Mettre en place un système de relance par email")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_user_experience()
