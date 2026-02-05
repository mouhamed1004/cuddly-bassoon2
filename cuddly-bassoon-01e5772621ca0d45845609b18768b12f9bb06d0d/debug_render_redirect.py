#!/usr/bin/env python3
"""
Script pour diagnostiquer le problème de redirection sur Render
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

def check_database_schema():
    """Vérifie le schéma de la base de données"""
    print("🔍 VÉRIFICATION DU SCHÉMA DE BASE DE DONNÉES")
    print("=" * 60)
    
    try:
        with connection.cursor() as cursor:
            # Vérifier la structure de la table notification
            cursor.execute("PRAGMA table_info(blizzgame_notification)")
            columns = cursor.fetchall()
            
            print("📋 Colonnes de la table blizzgame_notification:")
            order_column_exists = False
            for col in columns:
                col_name = col[1]
                col_type = col[2]
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

def test_notification_creation():
    """Teste la création d'une notification avec order"""
    print("\n🧪 TEST DE CRÉATION DE NOTIFICATION")
    print("=" * 60)
    
    try:
        # Récupérer un utilisateur et une commande
        user = User.objects.first()
        order = Order.objects.filter(user=user).first()
        
        if not user or not order:
            print("❌ Utilisateur ou commande non trouvé")
            return False
        
        print(f"👤 Utilisateur: {user.username}")
        print(f"📦 Commande: {order.order_number}")
        
        # Tenter de créer une notification avec order
        try:
            notification = Notification.objects.create(
                user=user,
                title="Test Notification",
                message="Test de notification avec order",
                notification_type="order_confirmation",
                order=order
            )
            print(f"✅ Notification créée avec succès: {notification.id}")
            print(f"   - Order: {notification.order}")
            print(f"   - Type: {notification.notification_type}")
            
            # Nettoyer
            notification.delete()
            print("   🧹 Notification de test supprimée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de notification: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_shop_payment_success():
    """Teste la vue shop_payment_success"""
    print("\n🎯 TEST DE LA VUE SHOP_PAYMENT_SUCCESS")
    print("=" * 60)
    
    try:
        # Récupérer un utilisateur et une commande
        user = User.objects.first()
        order = Order.objects.filter(user=user).first()
        
        if not user or not order:
            print("❌ Utilisateur ou commande non trouvé")
            return False
        
        print(f"👤 Utilisateur: {user.username}")
        print(f"📦 Commande: {order.order_number}")
        
        # Tester l'accès à la vue
        client = Client()
        client.force_login(user)
        
        success_url = reverse('shop_payment_success', kwargs={'order_id': order.id})
        print(f"🔗 URL de test: {success_url}")
        
        response = client.get(success_url)
        print(f"📊 Statut de réponse: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.url
            print(f"✅ Redirection vers: {redirect_url}")
            
            # Vérifier le type de redirection
            if 'my_orders' in redirect_url or 'shop/orders' in redirect_url:
                print("✅ Redirection correcte vers my_orders")
                return True
            elif 'shop/' in redirect_url:
                print("⚠️  Redirection vers shop/ (peut être correcte)")
                return True
            else:
                print(f"❌ Redirection inattendue: {redirect_url}")
                return False
        else:
            print(f"❌ Pas de redirection, statut: {response.status_code}")
            if hasattr(response, 'content'):
                content = response.content.decode()
                print(f"📝 Contenu: {content[:300]}...")
                
                # Chercher des erreurs spécifiques
                if "Not Found" in content:
                    print("🚨 ERREUR 'Not Found' détectée dans le contenu")
                if "order_id" in content:
                    print("🚨 Erreur liée à 'order_id' détectée")
                    
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_my_orders_access():
    """Teste l'accès à my_orders"""
    print("\n📋 TEST D'ACCÈS À MY_ORDERS")
    print("=" * 60)
    
    try:
        # Récupérer un utilisateur
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        print(f"👤 Utilisateur: {user.username}")
        
        # Tester l'accès à my_orders
        client = Client()
        client.force_login(user)
        
        my_orders_url = reverse('my_orders')
        print(f"🔗 URL my_orders: {my_orders_url}")
        
        response = client.get(my_orders_url)
        print(f"📊 Statut de réponse: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Accès à my_orders réussi")
            return True
        elif response.status_code == 302:
            redirect_url = response.url
            print(f"⚠️  Redirection vers: {redirect_url}")
            return True
        else:
            print(f"❌ Erreur d'accès: {response.status_code}")
            if hasattr(response, 'content'):
                content = response.content.decode()
                print(f"📝 Contenu: {content[:300]}...")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 DIAGNOSTIC COMPLET DE LA REDIRECTION RENDER")
    print("=" * 60)
    
    success = True
    
    # Test 1: Vérifier le schéma de la base de données
    if not check_database_schema():
        success = False
    
    # Test 2: Tester la création de notification
    if not test_notification_creation():
        success = False
    
    # Test 3: Tester l'accès à my_orders
    if not test_my_orders_access():
        success = False
    
    # Test 4: Tester shop_payment_success
    if not test_shop_payment_success():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ La redirection devrait fonctionner")
        print("✅ Le problème pourrait être ailleurs")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Des problèmes ont été détectés")
        print("⚠️  Il faut corriger les erreurs")
    
    print("\n🔧 RECOMMANDATIONS:")
    print("1. Vérifier que les migrations sont appliquées sur Render")
    print("2. Vérifier les logs de Render pour des erreurs spécifiques")
    print("3. Tester directement sur l'URL de production")

if __name__ == "__main__":
    main()
