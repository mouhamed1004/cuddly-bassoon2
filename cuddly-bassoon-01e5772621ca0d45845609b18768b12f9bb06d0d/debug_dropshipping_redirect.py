#!/usr/bin/env python3
"""
Script pour déboguer la redirection après achat dropshipping
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

def debug_dropshipping_redirect():
    """Débogue la redirection après achat dropshipping"""
    print("🔍 DÉBOGAGE DE LA REDIRECTION DROPSHIPPING")
    print("=" * 60)
    
    try:
        # Test 1: Vérifier que l'URL my_orders existe
        print("1. Test de l'URL my_orders...")
        try:
            my_orders_url = reverse('my_orders')
            print(f"   ✅ URL my_orders trouvée: {my_orders_url}")
        except Exception as e:
            print(f"   ❌ Erreur URL my_orders: {e}")
            return False
        
        # Test 2: Vérifier qu'un utilisateur existe
        print("\n2. Test des utilisateurs...")
        users = User.objects.all()
        if users.exists():
            user = users.first()
            print(f"   ✅ Utilisateur trouvé: {user.username}")
        else:
            print("   ❌ Aucun utilisateur trouvé")
            return False
        
        # Test 3: Vérifier qu'une commande existe
        print("\n3. Test des commandes...")
        orders = Order.objects.filter(user=user)
        if orders.exists():
            order = orders.first()
            print(f"   ✅ Commande trouvée: {order.order_number}")
        else:
            print("   ⚠️  Aucune commande trouvée pour cet utilisateur")
            # Créer une commande de test
            from blizzgame.models import Order
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
            print(f"   ✅ Commande de test créée: {order.order_number}")
        
        # Test 4: Tester l'accès à my_orders avec un client authentifié
        print("\n4. Test d'accès à my_orders...")
        client = Client()
        client.force_login(user)
        
        response = client.get(my_orders_url)
        print(f"   📊 Statut de réponse: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Accès à my_orders réussi")
        elif response.status_code == 302:
            redirect_url = response.url
            print(f"   ⚠️  Redirection vers: {redirect_url}")
        else:
            print(f"   ❌ Erreur d'accès: {response.status_code}")
            if hasattr(response, 'content'):
                print(f"   📝 Contenu: {response.content.decode()[:200]}...")
        
        # Test 5: Tester l'accès sans authentification
        print("\n5. Test d'accès sans authentification...")
        client = Client()  # Nouveau client non authentifié
        
        response = client.get(my_orders_url)
        print(f"   📊 Statut de réponse: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.url
            print(f"   ✅ Redirection attendue vers: {redirect_url}")
        else:
            print(f"   ❌ Comportement inattendu: {response.status_code}")
        
        # Test 6: Vérifier les URLs de paiement
        print("\n6. Test des URLs de paiement...")
        try:
            shop_payment_url = reverse('shop_payment', kwargs={'order_id': order.id})
            print(f"   ✅ URL shop_payment trouvée: {shop_payment_url}")
        except Exception as e:
            print(f"   ❌ Erreur URL shop_payment: {e}")
        
        try:
            shop_payment_success_url = reverse('shop_payment_success', kwargs={'order_id': order.id})
            print(f"   ✅ URL shop_payment_success trouvée: {shop_payment_success_url}")
        except Exception as e:
            print(f"   ❌ Erreur URL shop_payment_success: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du débogage: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redirect_flow():
    """Test le flux complet de redirection"""
    print(f"\n🧪 TEST DU FLUX DE REDIRECTION")
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
        
        # Simuler l'accès à shop_payment_success
        client = Client()
        client.force_login(user)
        
        success_url = reverse('shop_payment_success', kwargs={'order_id': order.id})
        print(f"🔗 URL de test: {success_url}")
        
        response = client.get(success_url)
        print(f"📊 Statut de réponse: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.url
            print(f"✅ Redirection vers: {redirect_url}")
            
            # Vérifier que c'est bien vers my_orders
            if 'my_orders' in redirect_url or 'shop/orders' in redirect_url:
                print("✅ Redirection correcte vers my_orders")
                return True
            else:
                print(f"❌ Redirection incorrecte: {redirect_url}")
                return False
        else:
            print(f"❌ Pas de redirection, statut: {response.status_code}")
            if hasattr(response, 'content'):
                print(f"📝 Contenu: {response.content.decode()[:200]}...")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 DÉBOGAGE DE LA REDIRECTION DROPSHIPPING")
    print("=" * 60)
    
    success = True
    
    # Débogage général
    if not debug_dropshipping_redirect():
        success = False
    
    # Test du flux de redirection
    if not test_redirect_flow():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 DÉBOGAGE TERMINÉ !")
        print("✅ Tous les tests sont passés")
        print("✅ La redirection devrait fonctionner")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Des problèmes ont été détectés")
        print("⚠️  Il faut corriger les erreurs")

if __name__ == "__main__":
    main()
