#!/usr/bin/env python3
"""
Script pour corriger la gestion des callbacks CinetPay
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
import requests

def fix_cinetpay_callbacks():
    """Corrige la gestion des callbacks CinetPay"""
    print("CORRECTION GESTION CALLBACKS CINETPAY")
    print("=" * 50)
    
    try:
        # 1. Vérifier les transactions en attente
        print("\n1. VERIFICATION TRANSACTIONS EN ATTENTE")
        print("-" * 40)
        
        pending_transactions = ShopCinetPayTransaction.objects.filter(status='pending').order_by('-created_at')
        print(f"Transactions en attente: {pending_transactions.count()}")
        
        for transaction in pending_transactions:
            print(f"\nTransaction: {transaction.cinetpay_transaction_id}")
            print(f"  Status: {transaction.status}")
            print(f"  Commande: #{transaction.order.order_number}")
            print(f"  Montant: {transaction.amount} {transaction.currency}")
            print(f"  Cree le: {transaction.created_at}")
            
            # Vérifier le statut sur CinetPay
            try:
                cinetpay_api = CinetPayAPI()
                verification_result = cinetpay_api.verify_payment(transaction.cinetpay_transaction_id)
                
                if verification_result:
                    payment_status = verification_result.get('data', {}).get('payment_status')
                    print(f"  Status CinetPay: {payment_status}")
                    
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
                        
                        # Créer la commande Shopify
                        from blizzgame.shopify_utils import create_shopify_order_from_blizz_order, mark_order_as_paid_in_shopify
                        
                        try:
                            shopify_order = create_shopify_order_from_blizz_order(order)
                            if shopify_order:
                                mark_order_as_paid_in_shopify(order)
                                print(f"  -> Commande Shopify creee: {order.shopify_order_id}")
                            else:
                                print("  -> ERREUR: Echec creation commande Shopify")
                        except Exception as e:
                            print(f"  -> ERREUR Shopify: {e}")
                        
                        print("  -> Transaction mise a jour avec succes!")
                        
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
                        print(f"  -> Status en attente: {payment_status}")
                        
                else:
                    print("  -> ERREUR: Impossible de verifier le statut")
                    
            except Exception as e:
                print(f"  -> ERREUR verification: {e}")
        
        # 2. Vérifier les URLs de callback
        print("\n2. VERIFICATION URLS DE CALLBACK")
        print("-" * 40)
        
        base_url = settings.BASE_URL
        callback_urls = {
            'notification_url': f"{base_url}/shop/cinetpay/notification/",
            'return_url': f"{base_url}/shop/payment/success/",
            'cancel_url': f"{base_url}/shop/payment/failed/"
        }
        
        print(f"Base URL: {base_url}")
        for name, url in callback_urls.items():
            print(f"{name}: {url}")
            
            # Tester l'accessibilité
            try:
                response = requests.head(url, timeout=10)
                print(f"  -> Status: {response.status_code}")
            except Exception as e:
                print(f"  -> ERREUR: {e}")
        
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
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_cinetpay_callbacks()
