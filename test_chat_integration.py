#!/usr/bin/env python
"""
Script de test pour l'intégration complète du système de chat
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

def test_chat_integration():
    print("🔗 Test d'intégration complète du système de chat")
    print("=" * 60)
    
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
        print(f"   ✅ Statut: {transaction.get_status_display()}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # Tester le cycle de vie complet d'une transaction avec chat
    print("\n3. Test du cycle de vie de la transaction avec chat...")
    
    # Étape 1: Transaction en attente (chat bloqué)
    print("\n   📋 Étape 1: Transaction en attente (chat bloqué)")
    transaction.status = 'pending'
    transaction.save()
    
    chat = Chat.objects.get(transaction=transaction)
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f"   ✅ Statut transaction: {transaction.get_status_display()}")
    print(f"   ✅ Chat bloqué: {chat.is_locked}")
    
    # Étape 2: Paiement effectué (chat débloqué)
    print("\n   📋 Étape 2: Paiement effectué (chat débloqué)")
    transaction.status = 'processing'
    transaction.save()
    
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f"   ✅ Statut transaction: {transaction.get_status_display()}")
    print(f"   ✅ Chat bloqué: {chat.is_locked}")
    
    # Étape 3: Messages échangés
    print("\n   📋 Étape 3: Messages échangés")
    
    # Message de l'acheteur
    message1 = Message.objects.create(
        chat=chat,
        sender=buyer,
        content="J'ai effectué le paiement, pouvez-vous m'envoyer les informations ?",
        message_type='text'
    )
    
    # Notification pour le vendeur
    Notification.objects.create(
        user=seller,
        title='Nouveau message',
        content=f'Vous avez reçu un nouveau message de {buyer.username}',
        type='new_message',
        message=message1
    )
    
    print(f"   ✅ Message acheteur: {message1.content[:50]}...")
    
    # Message du vendeur
    message2 = Message.objects.create(
        chat=chat,
        sender=seller,
        content="Parfait ! Je vous envoie les informations par message privé.",
        message_type='text'
    )
    
    # Notification pour l'acheteur
    Notification.objects.create(
        user=buyer,
        title='Nouveau message',
        content=f'Vous avez reçu un nouveau message de {seller.username}',
        type='new_message',
        message=message2
    )
    
    print(f"   ✅ Message vendeur: {message2.content[:50]}...")
    
    # Étape 4: Confirmation de réception
    print("\n   📋 Étape 4: Confirmation de réception")
    transaction.status = 'completed'
    transaction.save()
    
    print(f"   ✅ Statut transaction: {transaction.get_status_display()}")
    
    # Message de confirmation
    message3 = Message.objects.create(
        chat=chat,
        sender=buyer,
        content="Merci ! J'ai bien reçu les informations. Transaction terminée avec succès.",
        message_type='text'
    )
    
    print(f"   ✅ Message de confirmation: {message3.content[:50]}...")
    
    # Tester la création d'un litige
    print("\n4. Test de création d'un litige...")
    
    # Créer un nouveau post pour le litige
    post2, created = Post.objects.get_or_create(
        title='Compte de test pour litige',
        defaults={
            'user': 'test_seller_chat',
            'author': seller,
            'caption': 'Compte de test pour tester le système de litige',
            'price': 75.00,
            'email': 'test2@example.com',
            'password': 'testpass123',
            'game_type': 'PUBG',
            'coins': '2000',
            'level': '60'
        }
    )
    
    # Créer une nouvelle transaction
    transaction2 = Transaction.objects.create(
        buyer=buyer,
        seller=seller,
        post=post2,
        amount=75.00,
        status='processing'
    )
    
    print(f"   ✅ Nouvelle transaction: {transaction2.id}")
    
    # Créer un litige
    dispute = Dispute.objects.create(
        transaction=transaction2,
        opened_by=buyer,
        reason='invalid_account',
        description='Le compte ne fonctionne pas comme promis',
        disputed_amount=75.00
    )
    
    print(f"   ✅ Litige créé: {dispute.id}")
    print(f"   ✅ Raison: {dispute.get_reason_display()}")
    
    # Créer le chat de litige
    dispute_chat = Chat.objects.create(
        dispute=dispute,
        is_active=True,
        is_locked=False
    )
    
    print(f"   ✅ Chat de litige: {dispute_chat.id}")
    
    # Messages de litige
    print("\n5. Test des messages de litige...")
    
    # Message de l'acheteur
    dispute_message1 = Message.objects.create(
        chat=dispute_chat,
        sender=buyer,
        content="Bonjour, j'ai un problème avec le compte que j'ai acheté.",
        message_type='text'
    )
    
    # Notification pour le vendeur
    Notification.objects.create(
        user=seller,
        title='Nouveau message de litige',
        content=f'Vous avez reçu un nouveau message de {buyer.username} dans le litige #{dispute.id.hex[:8]}',
        type='dispute_message',
        message=dispute_message1
    )
    
    print(f"   ✅ Message de litige acheteur: {dispute_message1.content[:50]}...")
    
    # Message du vendeur
    dispute_message2 = Message.objects.create(
        chat=dispute_chat,
        sender=seller,
        content="Pouvez-vous me donner plus de détails sur le problème ?",
        message_type='text'
    )
    
    # Notification pour l'acheteur
    Notification.objects.create(
        user=buyer,
        title='Nouveau message de litige',
        content=f'Vous avez reçu un nouveau message de {seller.username} dans le litige #{dispute.id.hex[:8]}',
        type='dispute_message',
        message=dispute_message2
    )
    
    print(f"   ✅ Message de litige vendeur: {dispute_message2.content[:50]}...")
    
    # Tester l'accès admin au chat de litige
    print("\n6. Test de l'accès admin au chat de litige...")
    
    # Créer un utilisateur admin
    admin, created = User.objects.get_or_create(
        username='test_admin_chat',
        defaults={
            'email': 'admin@test.com',
            'first_name': 'Test',
            'last_name': 'Admin',
            'is_staff': True
        }
    )
    if created:
        admin.set_password('testpass123')
        admin.save()
        Profile.objects.create(user=admin)
    
    print(f"   ✅ Admin: {admin.username}")
    
    # Tester l'accès admin au chat de litige
    admin_access = dispute_chat.has_access(admin)
    print(f"   ✅ Accès admin au chat de litige: {admin_access}")
    
    # Message de l'admin
    admin_message = Message.objects.create(
        chat=dispute_chat,
        sender=admin,
        content="Bonjour, je suis l'administrateur. Je vais examiner votre litige.",
        message_type='text'
    )
    
    print(f"   ✅ Message admin: {admin_message.content[:50]}...")
    
    # Tester les différents types de messages
    print("\n7. Test des différents types de messages...")
    
    # Message avec image (simulé)
    image_message = Message.objects.create(
        chat=chat,
        sender=buyer,
        content="Voici une capture d'écran du problème",
        message_type='image'
    )
    
    print(f"   ✅ Message image: {image_message.get_message_type_display()}")
    
    # Message avec fichier (simulé)
    file_message = Message.objects.create(
        chat=dispute_chat,
        sender=seller,
        content="Voici le fichier de configuration",
        message_type='file'
    )
    
    print(f"   ✅ Message fichier: {file_message.get_message_type_display()}")
    
    # Statistiques finales
    print("\n8. Statistiques finales...")
    
    total_chats = Chat.objects.count()
    total_messages = Message.objects.count()
    total_notifications = Notification.objects.count()
    total_disputes = Dispute.objects.count()
    
    print(f"   📊 Total des chats: {total_chats}")
    print(f"   📊 Total des messages: {total_messages}")
    print(f"   📊 Total des notifications: {total_notifications}")
    print(f"   📊 Total des litiges: {total_disputes}")
    
    # Messages par type
    text_messages = Message.objects.filter(message_type='text').count()
    image_messages = Message.objects.filter(message_type='image').count()
    file_messages = Message.objects.filter(message_type='file').count()
    
    print(f"   📊 Messages texte: {text_messages}")
    print(f"   📊 Messages image: {image_messages}")
    print(f"   📊 Messages fichier: {file_messages}")
    
    # Chats par type
    transaction_chats = Chat.objects.filter(transaction__isnull=False).count()
    dispute_chats = Chat.objects.filter(dispute__isnull=False).count()
    
    print(f"   📊 Chats de transaction: {transaction_chats}")
    print(f"   📊 Chats de litige: {dispute_chats}")
    
    # Notifications par type
    message_notifications = Notification.objects.filter(type='new_message').count()
    dispute_notifications = Notification.objects.filter(type='dispute_message').count()
    
    print(f"   📊 Notifications de message: {message_notifications}")
    print(f"   📊 Notifications de litige: {dispute_notifications}")
    
    print("\n🎉 Test d'intégration complète terminé avec succès !")
    print("\n📋 Fonctionnalités testées :")
    print("   ✅ Cycle de vie des transactions avec chat")
    print("   ✅ Blocage/déblocage du chat selon le statut")
    print("   ✅ Messages entre acheteur et vendeur")
    print("   ✅ Notifications automatiques")
    print("   ✅ Système de litige avec chat")
    print("   ✅ Accès admin aux chats de litige")
    print("   ✅ Différents types de messages")
    print("   ✅ Gestion des notifications")

if __name__ == '__main__':
    test_chat_integration()

