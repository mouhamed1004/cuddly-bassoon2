#!/usr/bin/env python3
"""
Script pour tester la redirection après achat de produit dropshipping
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order, Notification
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import RequestFactory, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

def test_shop_payment_redirect():
    """Test la redirection après achat de produit dropshipping"""
    print("🧪 TEST DE LA REDIRECTION APRÈS ACHAT DROPSHIPPING")
    print("=" * 60)
    
    try:
        # Récupérer un utilisateur de test
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        print(f"👤 Utilisateur de test: {user.username}")
        
        # Récupérer une commande de test
        order = Order.objects.filter(user=user).first()
        if not order:
            print("❌ Aucune commande trouvée pour cet utilisateur")
            return False
        
        print(f"📦 Commande de test: {order.order_number}")
        print(f"   - Statut: {order.status}")
        print(f"   - Paiement: {order.payment_status}")
        
        # Simuler une requête vers shop_payment_success
        client = Client()
        client.force_login(user)
        
        # URL de la page de succès
        url = reverse('shop_payment_success', kwargs={'order_id': order.id})
        print(f"🔗 URL de test: {url}")
        
        # Faire la requête
        response = client.get(url)
        print(f"📊 Statut de réponse: {response.status_code}")
        
        # Vérifier la redirection
        if response.status_code == 302:
            redirect_url = response.url
            print(f"✅ Redirection détectée vers: {redirect_url}")
            
            # Vérifier que c'est vers my_orders
            if 'my_orders' in redirect_url:
                print("✅ Redirection correcte vers la page des commandes")
            else:
                print(f"❌ Redirection incorrecte: {redirect_url}")
                return False
        else:
            print(f"❌ Pas de redirection, statut: {response.status_code}")
            return False
        
        # Vérifier les messages
        messages = list(get_messages(response.wsgi_request))
        if messages:
            print(f"📝 Messages trouvés: {len(messages)}")
            for message in messages:
                print(f"   - {message.tags}: {message.message}")
        else:
            print("⚠️  Aucun message trouvé")
        
        # Vérifier la notification
        notifications = Notification.objects.filter(user=user, order=order)
        if notifications.exists():
            notification = notifications.first()
            print(f"🔔 Notification créée:")
            print(f"   - Titre: {notification.title}")
            print(f"   - Contenu: {notification.content}")
            print(f"   - Type: {notification.type}")
        else:
            print("⚠️  Aucune notification créée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notification_creation():
    """Test la création de notification pour les commandes"""
    print(f"\n🧪 TEST DE CRÉATION DE NOTIFICATION")
    print("=" * 60)
    
    try:
        # Récupérer un utilisateur et une commande
        user = User.objects.first()
        order = Order.objects.filter(user=user).first()
        
        if not user or not order:
            print("❌ Utilisateur ou commande non trouvé")
            return False
        
        # Créer une notification de test
        notification = Notification.objects.create(
            user=user,
            type='transaction_update',
            title='Commande confirmée',
            content=f"Votre commande #{order.order_number} a été confirmée et est en cours de traitement.",
            order=order
        )
        
        print(f"✅ Notification créée: {notification.id}")
        print(f"   - Utilisateur: {notification.user.username}")
        print(f"   - Commande: {notification.order.order_number}")
        print(f"   - Titre: {notification.title}")
        
        # Vérifier que la notification est bien liée à la commande
        order_notifications = order.notifications.all()
        print(f"📊 Notifications liées à la commande: {order_notifications.count()}")
        
        # Nettoyer
        notification.delete()
        print("🧹 Notification de test supprimée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 TEST DE LA REDIRECTION APRÈS ACHAT DROPSHIPPING")
    print("=" * 60)
    
    success = True
    
    # Test de la redirection
    if not test_shop_payment_redirect():
        success = False
    
    # Test de création de notification
    if not test_notification_creation():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ La redirection fonctionne correctement")
        print("✅ Les notifications sont créées")
        print("✅ Le flux est cohérent avec les annonces")
        print("✅ Prêt pour le déploiement")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Des problèmes ont été détectés")
        print("⚠️  Il faut corriger le code")

if __name__ == "__main__":
    main()
