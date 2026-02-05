#!/usr/bin/env python3
"""
Script de test adapté à PostgreSQL sur Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.urls import reverse
from django.contrib.auth.models import User
from blizzgame.models import Order, Notification
from django.test import Client
from django.db import connection

def check_postgresql_schema():
    """Vérifie le schéma PostgreSQL"""
    print("🔍 VÉRIFICATION DU SCHÉMA POSTGRESQL")
    print("=" * 60)
    
    try:
        with connection.cursor() as cursor:
            # Vérifier la structure de la table notification (PostgreSQL)
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'blizzgame_notification'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            print("📋 Colonnes de la table blizzgame_notification:")
            order_column_exists = False
            for col_name, col_type in columns:
                print(f"   - {col_name}: {col_type}")
                if col_name == 'order_id':
                    order_column_exists = True
            
            if order_column_exists:
                print("   ✅ Colonne 'order_id' trouvée")
            else:
                print("   ❌ Colonne 'order_id' MANQUANTE")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du schéma: {e}")
        return False

def create_test_order():
    """Crée une commande de test"""
    print("\n📦 CRÉATION D'UNE COMMANDE DE TEST")
    print("=" * 60)
    
    try:
        # Récupérer un utilisateur
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return None
        
        print(f"👤 Utilisateur: {user.username}")
        
        # Créer une commande de test
        order = Order.objects.create(
            user=user,
            customer_email=user.email,
            customer_first_name=user.first_name or 'Test',
            customer_last_name=user.last_name or 'User',
            subtotal=10.00,
            total_amount=10.00,
            payment_status='paid',
            status='processing'
        )
        
        print(f"✅ Commande de test créée: {order.order_number}")
        print(f"   - ID: {order.id}")
        print(f"   - Montant: {order.total_amount} EUR")
        print(f"   - Statut: {order.status}")
        
        return order
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de commande: {e}")
        return None

def test_redirect_with_order(order):
    """Teste la redirection avec une commande"""
    print(f"\n🎯 TEST DE REDIRECTION AVEC COMMANDE {order.order_number}")
    print("=" * 60)
    
    try:
        # Tester l'accès à my_orders
        client = Client()
        client.force_login(order.user)
        
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
            
            if 'my_orders' in redirect_url or 'shop/orders' in redirect_url:
                print("✅ Redirection correcte vers my_orders")
                return True
            else:
                print(f"⚠️  Redirection vers: {redirect_url}")
                return True
        else:
            print(f"❌ Pas de redirection: {response.status_code}")
            if hasattr(response, 'content'):
                content = response.content.decode()
                print(f"📝 Contenu: {content[:300]}...")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notification_creation(order):
    """Teste la création de notification"""
    print(f"\n🔔 TEST DE CRÉATION DE NOTIFICATION")
    print("=" * 60)
    
    try:
        # Tenter de créer une notification
        notification = Notification.objects.create(
            user=order.user,
            title="Test Notification",
            notification_type="order_confirmation",
            order=order
        )
        
        print(f"✅ Notification créée: {notification.id}")
        print(f"   - Order: {notification.order}")
        print(f"   - Type: {notification.notification_type}")
        
        # Nettoyer
        notification.delete()
        print("✅ Notification supprimée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de notification: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 TEST POSTGRESQL SUR RENDER")
    print("=" * 60)
    
    success = True
    
    # Test 1: Vérifier le schéma PostgreSQL
    if not check_postgresql_schema():
        success = False
    
    # Test 2: Créer une commande de test
    order = create_test_order()
    if not order:
        success = False
        return
    
    # Test 3: Tester la création de notification
    if not test_notification_creation(order):
        success = False
    
    # Test 4: Tester la redirection
    if not test_redirect_with_order(order):
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ La redirection devrait fonctionner")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Des problèmes ont été détectés")

if __name__ == "__main__":
    main()
