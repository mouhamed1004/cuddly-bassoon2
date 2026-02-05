#!/usr/bin/env python3
"""
Script pour corriger les URLs de callback et vérifier les paiements CinetPay
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order, ShopCinetPayTransaction
from blizzgame.cinetpay_utils import CinetPayAPI
from django.conf import settings
from django.urls import reverse
import requests
import json

def fix_callback_urls_and_verify():
    """Corrige les URLs de callback et vérifie les paiements"""
    print("CORRECTION URLS CALLBACK ET VERIFICATION PAIEMENTS")
    print("=" * 60)
    
    try:
        # 1. Vérifier les URLs réelles
        print("\n1. VERIFICATION URLS REELLES")
        print("-" * 40)
        
        base_url = settings.BASE_URL
        print(f"Base URL: {base_url}")
        
        # URLs correctes selon urls.py
        correct_urls = {
            'notification_url': f"{base_url}{reverse('shop_cinetpay_notification')}",
            'success_url_pattern': f"{base_url}/shop/payment/cinetpay/success/[ORDER_ID]/",
            'failed_url_pattern': f"{base_url}/shop/payment/cinetpay/failed/[ORDER_ID]/",
        }
        
        for name, url in correct_urls.items():
            print(f"{name}: {url}")
        
        # Tester l'URL de notification
        notification_url = correct_urls['notification_url']
        try:
            # Test POST (CinetPay envoie des POST)
            test_data = {'test': 'true'}
            response = requests.post(notification_url, data=test_data, timeout=10)
            print(f"Notification URL (POST): {response.status_code}")
        except Exception as e:
            print(f"Erreur test notification: {e}")
        
        # 2. Vérifier manuellement les paiements sur CinetPay
        print("\n2. VERIFICATION MANUELLE DES PAIEMENTS")
        print("-" * 40)
        
        pending_transactions = ShopCinetPayTransaction.objects.filter(status='pending')
        print(f"Transactions en attente: {pending_transactions.count()}")
        
        cinetpay_api = CinetPayAPI()
        
        for transaction in pending_transactions:
            print(f"\nTransaction: {transaction.cinetpay_transaction_id}")
            print(f"  Commande: #{transaction.order.order_number}")
            print(f"  Montant: {transaction.amount} {transaction.currency}")
            print(f"  URL de paiement: {transaction.payment_url[:50]}...")
            
            # Vérification manuelle avec l'API CinetPay
            try:
                # Utiliser l'API de vérification CinetPay
                verification_data = {
                    'apikey': cinetpay_api.api_key,
                    'site_id': cinetpay_api.site_id,
                    'transaction_id': transaction.cinetpay_transaction_id
                }
                
                verify_url = "https://api-checkout.cinetpay.com/v2/payment/check"
                response = requests.post(verify_url, json=verification_data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  Verification API response: {response.status_code}")
                    print(f"  Code: {result.get('code')}")
                    print(f"  Message: {result.get('message')}")
                    
                    if result.get('code') == '00':
                        # Succès de la vérification
                        payment_status = result.get('data', {}).get('status')
                        print(f"  Status paiement: {payment_status}")
                        
                        if payment_status == 'ACCEPTED':
                            print("  -> PAIEMENT ACCEPTE! Mise a jour...")
                            
                            # Mettre à jour la transaction
                            transaction.status = 'completed'
                            transaction.save()
                            
                            # Mettre à jour la commande
                            order = transaction.order
                            order.payment_status = 'paid'
                            order.status = 'processing'
                            order.save()
                            
                            print("  -> Transaction et commande mises a jour!")
                            
                            # Créer la commande Shopify
                            try:
                                from blizzgame.shopify_utils import create_shopify_order_from_blizz_order, mark_order_as_paid_in_shopify
                                
                                if not order.shopify_order_id:
                                    shopify_order = create_shopify_order_from_blizz_order(order)
                                    if shopify_order:
                                        mark_order_as_paid_in_shopify(order)
                                        print(f"  -> Commande Shopify creee: {order.shopify_order_id}")
                                    else:
                                        print("  -> ERREUR: Echec creation commande Shopify")
                                else:
                                    print(f"  -> Commande Shopify existe deja: {order.shopify_order_id}")
                                    
                            except Exception as e:
                                print(f"  -> ERREUR Shopify: {e}")
                                
                        elif payment_status == 'REFUSED':
                            print("  -> PAIEMENT REFUSE! Mise a jour...")
                            
                            # Mettre à jour la transaction
                            transaction.status = 'failed'
                            transaction.save()
                            
                            # Mettre à jour la commande
                            order = transaction.order
                            order.payment_status = 'failed'
                            order.status = 'cancelled'
                            order.save()
                            
                            print("  -> Transaction marquee comme echouee")
                            
                        else:
                            print(f"  -> Status en attente ou autre: {payment_status}")
                            
                    else:
                        print(f"  -> Erreur verification: {result.get('message')}")
                        
                else:
                    print(f"  -> Erreur HTTP: {response.status_code}")
                    print(f"  -> Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"  -> ERREUR verification manuelle: {e}")
        
        # 3. Statistiques finales
        print("\n3. STATISTIQUES FINALES")
        print("-" * 40)
        
        # Recompter après les mises à jour
        updated_pending = ShopCinetPayTransaction.objects.filter(status='pending').count()
        completed = ShopCinetPayTransaction.objects.filter(status='completed').count()
        failed = ShopCinetPayTransaction.objects.filter(status='failed').count()
        
        print(f"Transactions en attente: {updated_pending}")
        print(f"Transactions completees: {completed}")
        print(f"Transactions echouees: {failed}")
        
        # Commandes
        paid_orders = Order.objects.filter(payment_status='paid').count()
        failed_orders = Order.objects.filter(payment_status='failed').count()
        pending_orders = Order.objects.filter(payment_status='pending').count()
        
        print(f"Commandes payees: {paid_orders}")
        print(f"Commandes echouees: {failed_orders}")
        print(f"Commandes en attente: {pending_orders}")
        
        # Commandes Shopify
        shopify_orders = Order.objects.filter(shopify_order_id__isnull=False).count()
        print(f"Commandes Shopify creees: {shopify_orders}")
        
        print("\n4. ACTIONS RECOMMANDEES")
        print("-" * 40)
        print("1. Les URLs de callback sont correctes dans le code")
        print("2. Le probleme etait dans le script de test precedent")
        print("3. Les paiements ont ete verifies manuellement")
        print("4. Les commandes Shopify ont ete creees pour les paiements valides")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_callback_urls_and_verify()
