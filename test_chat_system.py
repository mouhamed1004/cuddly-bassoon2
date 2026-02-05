#!/usr/bin/env python
"""
Script de test pour le système de chat avec Django Channels
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Post, Transaction, Chat, Message, Dispute, Profile
from django.utils import timezone
import uuid

def test_chat_system():
    print("🧪 Test du système de chat avec Django Channels")
    print("=" * 50)
    
    # Créer des utilisateurs de test
    print("\n1. Création des utilisateurs de test...")
    buyer, created = User.objects.get_or_create(
        username='test_buyer_chat',
        defaults={
            'email': 'buyer@test.com',
            'first_name': 'Test',
            'last_name': 'Buyer'
        }
    )
    if created:
        buyer.set_password('testpass123')
        buyer.save()
        Profile.objects.create(user=buyer)
    
    seller, created = User.objects.get_or_create(
        username='test_seller_chat',
        defaults={
            'email': 'seller@test.com',
            'first_name': 'Test',
            'last_name': 'Seller'
        }
    )
    if created:
        seller.set_password('testpass123')
        seller.save()
        Profile.objects.create(user=seller)
    
    print(f"   ✅ Acheteur: {buyer.username}")
    print(f"   ✅ Vendeur: {seller.username}")
    
    # Créer un post de test
    print("\n2. Création d'un post de test...")
    post, created = Post.objects.get_or_create(
        title='Compte de test pour chat',
        defaults={
            'user': 'test_seller_chat',
            'author': seller,
            'caption': 'Compte de test pour tester le système de chat',
            'price': 50.00,
            'email': 'test@example.com',
            'password': 'testpass123',
            'game_type': 'FreeFire',
            'coins': '1000',
            'level': '50'
        }
    )
    print(f"   ✅ Post: {post.title}")
    
    # Créer une transaction de test
    print("\n3. Création d'une transaction de test...")
    transaction, created = Transaction.objects.get_or_create(
        buyer=buyer,
        seller=seller,
        post=post,
        defaults={
            'amount': 50.00,
            'status': 'processing'
        }
    )
    print(f"   ✅ Transaction: {transaction.id}")
    print(f"   ✅ Statut: {transaction.get_status_display()}")
    
    # Créer un chat pour la transaction
    print("\n4. Création du chat de transaction...")
    chat, created = Chat.objects.get_or_create(
        transaction=transaction,
        defaults={
            'is_active': True,
            'is_locked': transaction.status in ['pending', 'waiting_payment']
        }
    )
    print(f"   ✅ Chat: {chat.id}")
    print(f"   ✅ Actif: {chat.is_active}")
    print(f"   ✅ Bloqué: {chat.is_locked}")
    
    # Tester les méthodes du chat
    print("\n5. Test des méthodes du chat...")
    print(f"   ✅ Accès acheteur: {chat.has_access(buyer)}")
    print(f"   ✅ Accès vendeur: {chat.has_access(seller)}")
    print(f"   ✅ Autres utilisateurs (acheteur): {[u.username for u in chat.get_other_users(buyer)]}")
    print(f"   ✅ Autres utilisateurs (vendeur): {[u.username for u in chat.get_other_users(seller)]}")
    print(f"   ✅ Autre utilisateur (acheteur): {chat.get_other_user(buyer).username if chat.get_other_user(buyer) else 'None'}")
    print(f"   ✅ Autre utilisateur (vendeur): {chat.get_other_user(seller).username if chat.get_other_user(seller) else 'None'}")
    
    # Créer des messages de test
    print("\n6. Création de messages de test...")
    messages_data = [
        {'sender': buyer, 'content': 'Bonjour, je suis intéressé par ce compte', 'type': 'text'},
        {'sender': seller, 'content': 'Salut ! Oui, c\'est un excellent compte', 'type': 'text'},
        {'sender': buyer, 'content': 'Parfait, je vais procéder au paiement', 'type': 'text'},
        {'sender': seller, 'content': 'D\'accord, je vous enverrai les informations après paiement', 'type': 'text'},
    ]
    
    for msg_data in messages_data:
        message = Message.objects.create(
            chat=chat,
            sender=msg_data['sender'],
            content=msg_data['content'],
            message_type=msg_data['type']
        )
        print(f"   ✅ Message de {message.sender.username}: {message.content[:30]}...")
    
    # Tester la création d'un litige
    print("\n7. Test de création d'un litige...")
    dispute, created = Dispute.objects.get_or_create(
        transaction=transaction,
        defaults={
            'opened_by': buyer,
            'reason': 'invalid_account',
            'description': 'Le compte ne fonctionne pas comme promis',
            'disputed_amount': 50.00
        }
    )
    print(f"   ✅ Litige: {dispute.id}")
    print(f"   ✅ Statut: {dispute.get_status_display()}")
    
    # Créer un chat pour le litige
    print("\n8. Création du chat de litige...")
    dispute_chat, created = Chat.objects.get_or_create(
        dispute=dispute,
        defaults={
            'is_active': True,
            'is_locked': False
        }
    )
    print(f"   ✅ Chat de litige: {dispute_chat.id}")
    print(f"   ✅ Actif: {dispute_chat.is_active}")
    print(f"   ✅ Bloqué: {dispute_chat.is_locked}")
    
    # Tester les méthodes du chat de litige
    print("\n9. Test des méthodes du chat de litige...")
    print(f"   ✅ Accès acheteur: {dispute_chat.has_access(buyer)}")
    print(f"   ✅ Accès vendeur: {dispute_chat.has_access(seller)}")
    print(f"   ✅ Autres utilisateurs (acheteur): {[u.username for u in dispute_chat.get_other_users(buyer)]}")
    print(f"   ✅ Autres utilisateurs (vendeur): {[u.username for u in dispute_chat.get_other_users(seller)]}")
    
    # Créer des messages de litige
    print("\n10. Création de messages de litige...")
    dispute_messages_data = [
        {'sender': buyer, 'content': 'J\'ai un problème avec le compte', 'type': 'text'},
        {'sender': seller, 'content': 'Pouvez-vous me donner plus de détails ?', 'type': 'text'},
        {'sender': buyer, 'content': 'Le compte ne se connecte pas', 'type': 'text'},
    ]
    
    for msg_data in dispute_messages_data:
        message = Message.objects.create(
            chat=dispute_chat,
            sender=msg_data['sender'],
            content=msg_data['content'],
            message_type=msg_data['type']
        )
        print(f"   ✅ Message de {message.sender.username}: {message.content[:30]}...")
    
    # Tester le blocage du chat
    print("\n11. Test du blocage du chat...")
    transaction.status = 'pending'
    transaction.save()
    
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f"   ✅ Transaction statut: {transaction.get_status_display()}")
    print(f"   ✅ Chat bloqué: {chat.is_locked}")
    
    # Tester le déblocage du chat
    print("\n12. Test du déblocage du chat...")
    transaction.status = 'processing'
    transaction.save()
    
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f"   ✅ Transaction statut: {transaction.get_status_display()}")
    print(f"   ✅ Chat bloqué: {chat.is_locked}")
    
    # Statistiques finales
    print("\n13. Statistiques finales...")
    print(f"   ✅ Nombre de chats: {Chat.objects.count()}")
    print(f"   ✅ Nombre de messages: {Message.objects.count()}")
    print(f"   ✅ Nombre de litiges: {Dispute.objects.count()}")
    print(f"   ✅ Messages de transaction: {Message.objects.filter(chat__transaction__isnull=False).count()}")
    print(f"   ✅ Messages de litige: {Message.objects.filter(chat__dispute__isnull=False).count()}")
    
    print("\n🎉 Test du système de chat terminé avec succès !")
    print("\n📋 Prochaines étapes :")
    print("   1. Tester l'interface WebSocket")
    print("   2. Vérifier les notifications")
    print("   3. Tester l'upload d'images")
    print("   4. Vérifier l'intégration avec les transactions")

if __name__ == '__main__':
    test_chat_system()

