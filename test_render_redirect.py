#!/usr/bin/env python3
"""
Script simple pour tester la redirection sur Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.urls import reverse
from django.contrib.auth.models import User
from blizzgame.models import Order
from django.test import Client

def test_simple():
    """Test simple de la redirection"""
    print("🧪 TEST SIMPLE DE REDIRECTION")
    print("=" * 40)
    
    try:
        # Récupérer un utilisateur et une commande
        user = User.objects.first()
        order = Order.objects.filter(user=user).first()
        
        if not user or not order:
            print("❌ Utilisateur ou commande non trouvé")
            return False
        
        print(f"👤 Utilisateur: {user.username}")
        print(f"📦 Commande: {order.order_number}")
        
        # Tester l'accès à my_orders
        client = Client()
        client.force_login(user)
        
        my_orders_url = reverse('my_orders')
        print(f"🔗 URL my_orders: {my_orders_url}")
        
        response = client.get(my_orders_url)
        print(f"📊 Statut my_orders: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur my_orders: {response.status_code}")
            return False
        
        # Tester shop_payment_success
        success_url = reverse('shop_payment_success', kwargs={'order_id': order.id})
        print(f"🔗 URL success: {success_url}")
        
        response = client.get(success_url)
        print(f"📊 Statut success: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.url
            print(f"✅ Redirection: {redirect_url}")
            return True
        else:
            print(f"❌ Pas de redirection: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_simple()
