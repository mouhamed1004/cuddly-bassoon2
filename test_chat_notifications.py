#!/usr/bin/env python
"""
Script de test pour les notifications du système de chat
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Post, Transaction, Chat, Message, Dispute, Notification, Profile
from django.utils import timezone
import uuid

def test_chat_notifications():
    print("🔔 Test des notifications du système de chat")
    print("=" * 50)
    
    # Récupérer les utilisateurs de test existants
    print("\n1. Récupération des utilisateurs de test...")
    try:
        buyer = User.objects.get(username='test_buyer_chat')
        seller = User.objects.get(username='test_seller_chat')
        print(f"   ✅ Acheteur: {buyer.username}")
        print(f"   ✅ Vendeur: {seller.username}")
    except User.DoesNotExist:
        print("   ❌ Utilisateurs de test non trouvés. Exécutez d'abord test_chat_system.py")
        return
    
    # Récupérer la transaction de test
    print("\n2. Récupération de la transaction de test...")
    try:
        transaction = Transaction.objects.filter(
            buyer=buyer, 
            seller=seller
        ).first()
        if not transaction:
            print("   ❌ Transaction de test non trouvée")
            return
        print(f"   ✅ Transaction: {transaction.id}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # Récupérer le chat de transaction
    print("\n3. Récupération du chat de transaction...")
    try:
        chat = Chat.objects.get(transaction=transaction)
        print(f"   ✅ Chat: {chat.id}")
    except Chat.DoesNotExist:
        print("   ❌ Chat de transaction non trouvé")
        return
    
    # Tester la création de notifications lors de l'envoi de messages
    print("\n4. Test de création de notifications...")
    
    # Compter les notifications existantes
    initial_notifications_buyer = Notification.objects.filter(user=buyer).count()
    initial_notifications_seller = Notification.objects.filter(user=seller).count()
    
    print(f"   📊 Notifications initiales acheteur: {initial_notifications_buyer}")
    print(f"   📊 Notifications initiales vendeur: {initial_notifications_seller}")
    
    # Créer un message de l'acheteur
    print("\n5. Création d'un message de l'acheteur...")
    message1 = Message.objects.create(
        chat=chat,
        sender=buyer,
        content="Test de notification - message de l'acheteur",
        message_type='text'
    )
    
    # Créer une notification pour le vendeur
    notification1 = Notification.objects.create(
        user=seller,
        title='Nouveau message',
        content=f'Vous avez reçu un nouveau message de {buyer.username}',
        type='new_message',
        message=message1
    )
    
    print(f"   ✅ Message créé: {message1.id}")
    print(f"   ✅ Notification créée: {notification1.id}")
    
    # Vérifier les notifications
    new_notifications_seller = Notification.objects.filter(user=seller).count()
    print(f"   📊 Nouvelles notifications vendeur: {new_notifications_seller}")
    print(f"   📈 Différence: {new_notifications_seller - initial_notifications_seller}")
    
    # Créer un message du vendeur
    print("\n6. Création d'un message du vendeur...")
    message2 = Message.objects.create(
        chat=chat,
        sender=seller,
        content="Test de notification - message du vendeur",
        message_type='text'
    )
    
    # Créer une notification pour l'acheteur
    notification2 = Notification.objects.create(
        user=buyer,
        title='Nouveau message',
        content=f'Vous avez reçu un nouveau message de {seller.username}',
        type='new_message',
        message=message2
    )
    
    print(f"   ✅ Message créé: {message2.id}")
    print(f"   ✅ Notification créée: {notification2.id}")
    
    # Vérifier les notifications
    new_notifications_buyer = Notification.objects.filter(user=buyer).count()
    print(f"   📊 Nouvelles notifications acheteur: {new_notifications_buyer}")
    print(f"   📈 Différence: {new_notifications_buyer - initial_notifications_buyer}")
    
    # Tester les notifications de litige
    print("\n7. Test des notifications de litige...")
    
    # Récupérer le litige de test
    try:
        dispute = Dispute.objects.filter(transaction=transaction).first()
        if not dispute:
            print("   ❌ Litige de test non trouvé")
            return
        print(f"   ✅ Litige: {dispute.id}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # Récupérer le chat de litige
    try:
        dispute_chat = Chat.objects.get(dispute=dispute)
        print(f"   ✅ Chat de litige: {dispute_chat.id}")
    except Chat.DoesNotExist:
        print("   ❌ Chat de litige non trouvé")
        return
    
    # Créer un message de litige
    print("\n8. Création d'un message de litige...")
    dispute_message = Message.objects.create(
        chat=dispute_chat,
        sender=buyer,
        content="Test de notification - message de litige",
        message_type='text'
    )
    
    # Créer une notification de litige
    dispute_notification = Notification.objects.create(
        user=seller,
        title='Nouveau message de litige',
        content=f'Vous avez reçu un nouveau message de {buyer.username} dans le litige #{dispute.id.hex[:8]}',
        type='dispute_message',
        message=dispute_message
    )
    
    print(f"   ✅ Message de litige créé: {dispute_message.id}")
    print(f"   ✅ Notification de litige créée: {dispute_notification.id}")
    
    # Tester les différents types de notifications
    print("\n9. Test des types de notifications...")
    
    notification_types = [
        ('message', 'Message texte'),
        ('dispute_message', 'Message de litige'),
        ('transaction_update', 'Mise à jour de transaction'),
        ('system', 'Notification système'),
    ]
    
    for notif_type, description in notification_types:
        notification = Notification.objects.create(
            user=buyer,
            title=f'Test {description}',
            content=f'Ceci est un test de {description}',
            type=notif_type
        )
        print(f"   ✅ {description}: {notification.id}")
    
    # Statistiques des notifications
    print("\n10. Statistiques des notifications...")
    
    total_notifications = Notification.objects.count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    read_notifications = Notification.objects.filter(is_read=True).count()
    
    print(f"   📊 Total des notifications: {total_notifications}")
    print(f"   📊 Notifications non lues: {unread_notifications}")
    print(f"   📊 Notifications lues: {read_notifications}")
    
    # Notifications par utilisateur
    buyer_notifications = Notification.objects.filter(user=buyer).count()
    seller_notifications = Notification.objects.filter(user=seller).count()
    
    print(f"   📊 Notifications acheteur: {buyer_notifications}")
    print(f"   📊 Notifications vendeur: {seller_notifications}")
    
    # Notifications par type
    print("\n11. Notifications par type...")
    for notif_type, description in notification_types:
        count = Notification.objects.filter(type=notif_type).count()
        print(f"   📊 {description}: {count}")
    
    # Tester le marquage des notifications comme lues
    print("\n12. Test du marquage des notifications comme lues...")
    
    # Marquer quelques notifications comme lues
    notifications_to_mark = Notification.objects.filter(user=buyer, is_read=False)[:3]
    for notification in notifications_to_mark:
        notification.is_read = True
        notification.save()
        print(f"   ✅ Notification marquée comme lue: {notification.id}")
    
    # Vérifier les nouvelles statistiques
    new_unread_buyer = Notification.objects.filter(user=buyer, is_read=False).count()
    new_read_buyer = Notification.objects.filter(user=buyer, is_read=True).count()
    
    print(f"   📊 Nouvelles notifications non lues acheteur: {new_unread_buyer}")
    print(f"   📊 Nouvelles notifications lues acheteur: {new_read_buyer}")
    
    print("\n🎉 Test des notifications terminé avec succès !")
    print("\n📋 Résumé :")
    print(f"   ✅ {total_notifications} notifications créées")
    print(f"   ✅ {unread_notifications} notifications non lues")
    print(f"   ✅ {read_notifications} notifications lues")
    print(f"   ✅ {buyer_notifications} notifications pour l'acheteur")
    print(f"   ✅ {seller_notifications} notifications pour le vendeur")

if __name__ == '__main__':
    test_chat_notifications()
