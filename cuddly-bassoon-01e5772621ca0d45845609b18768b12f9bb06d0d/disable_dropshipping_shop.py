#!/usr/bin/env python3
"""
Script pour désactiver complètement la boutique dropshipping
"""

import os
import sys
import django

# Configuration Django
sys.path.append('/opt/render/project/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Product, Order, CartItem, ShopCinetPayTransaction
from django.contrib.auth.models import User

def disable_dropshipping_shop():
    """
    Désactive complètement la boutique dropshipping
    """
    print("DESACTIVATION BOUTIQUE DROPSHIPPING")
    print("=" * 50)
    
    # 1. Désactiver tous les produits de la boutique
    print("\n1. DESACTIVATION PRODUITS BOUTIQUE")
    print("-" * 40)
    
    shop_products = Product.objects.filter(
        shopify_product_id__isnull=False
    )
    
    print(f"Produits boutique trouvés: {shop_products.count()}")
    
    for product in shop_products:
        product.status = 'inactive'
        product.save()
        print(f"  ✅ {product.name} - Désactivé")
    
    # 2. Nettoyer les paniers
    print("\n2. NETTOYAGE PANIERS")
    print("-" * 40)
    
    cart_items = CartItem.objects.all()
    print(f"Articles en panier: {cart_items.count()}")
    
    for item in cart_items:
        item.delete()
        print(f"  ✅ Panier nettoyé pour {item.user.username if item.user else 'Anonyme'}")
    
    # 3. Analyser les commandes en cours
    print("\n3. ANALYSE COMMANDES EN COURS")
    print("-" * 40)
    
    pending_orders = Order.objects.filter(
        status__in=['pending', 'processing']
    )
    
    print(f"Commandes en cours: {pending_orders.count()}")
    
    for order in pending_orders:
        print(f"  📦 {order.order_number}")
        print(f"     Client: {order.customer_email}")
        print(f"     Montant: {order.total_amount}€")
        print(f"     Status: {order.status}")
        print(f"     Créée: {order.created_at}")
        print()
    
    # 4. Analyser les transactions CinetPay
    print("\n4. ANALYSE TRANSACTIONS CINETPAY")
    print("-" * 40)
    
    cinetpay_transactions = ShopCinetPayTransaction.objects.all()
    print(f"Transactions CinetPay: {cinetpay_transactions.count()}")
    
    pending_transactions = cinetpay_transactions.filter(status='pending')
    print(f"Transactions en attente: {pending_transactions.count()}")
    
    completed_transactions = cinetpay_transactions.filter(status='completed')
    print(f"Transactions complétées: {completed_transactions.count()}")
    
    failed_transactions = cinetpay_transactions.filter(status='failed')
    print(f"Transactions échouées: {failed_transactions.count()}")
    
    # 5. Recommandations
    print("\n5. RECOMMANDATIONS")
    print("-" * 40)
    print("✅ Produits boutique désactivés")
    print("✅ Paniers nettoyés")
    print("📋 Commandes en cours à traiter manuellement")
    print("💳 Transactions CinetPay à vérifier")
    print()
    print("🔧 ACTIONS SUIVANTES:")
    print("1. Supprimer les liens de navigation vers la boutique")
    print("2. Désactiver les URLs de la boutique")
    print("3. Ajouter un message 'Boutique temporairement fermée'")
    print("4. Traiter manuellement les commandes en cours")
    print("5. Rembourser les transactions échouées si nécessaire")

if __name__ == "__main__":
    disable_dropshipping_shop()
