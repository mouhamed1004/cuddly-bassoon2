#!/usr/bin/env python
"""
Script pour simuler le processus de paiement complet
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Transaction, Chat, Message, Notification
from django.contrib.auth.models import User

def simulate_payment_process():
    print('💳 Simulation du processus de paiement complet')
    print('=' * 60)
    
    # Récupérer la transaction de ftr1
    transaction = Transaction.objects.get(id='17acf02c-f856-4de6-91fa-fae4d027a970')
    chat = Chat.objects.get(transaction=transaction)
    buyer = transaction.buyer
    seller = transaction.seller
    
    print(f'👤 Acheteur: {buyer.username}')
    print(f'👤 Vendeur: {seller.username}')
    print(f'💰 Montant: {transaction.amount}€')
    
    # Étape 1: Transaction en attente (chat bloqué)
    print(f'\n📋 Étape 1: Transaction en attente de paiement')
    transaction.status = 'pending'
    transaction.save()
    
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f'   ✅ Statut: {transaction.get_status_display()}')
    print(f'   🔒 Chat bloqué: {chat.is_locked}')
    print(f'   💬 Messages possibles: Non (chat bloqué)')
    
    # Étape 2: Paiement en cours
    print(f'\n📋 Étape 2: Paiement en cours de traitement')
    transaction.status = 'processing'
    transaction.save()
    
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f'   ✅ Statut: {transaction.get_status_display()}')
    print(f'   🔓 Chat débloqué: {not chat.is_locked}')
    print(f'   💬 Messages possibles: Oui (chat ouvert)')
    
    # Ajouter un message de confirmation de paiement
    payment_message = Message.objects.create(
        chat=chat,
        sender=buyer,
        content='J\'ai effectué le paiement, pouvez-vous confirmer la réception ?',
        message_type='text'
    )
    
    # Notification pour le vendeur
    Notification.objects.create(
        user=seller,
        title='Paiement effectué',
        content=f'{buyer.username} a effectué le paiement de {transaction.amount}€',
        type='transaction_update',
        message=payment_message
    )
    
    print(f'   ✅ Message de paiement envoyé')
    print(f'   🔔 Notification envoyée au vendeur')
    
    # Étape 3: Confirmation de réception
    print(f'\n📋 Étape 3: Confirmation de réception par le vendeur')
    transaction.status = 'completed'
    transaction.save()
    
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f'   ✅ Statut: {transaction.get_status_display()}')
    print(f'   🔓 Chat débloqué: {not chat.is_locked}')
    
    # Ajouter un message de confirmation
    confirmation_message = Message.objects.create(
        chat=chat,
        sender=seller,
        content='Paiement confirmé ! Je vous envoie les informations du compte par message privé.',
        message_type='text'
    )
    
    # Notification pour l'acheteur
    Notification.objects.create(
        user=buyer,
        title='Transaction terminée',
        content=f'Votre transaction avec {seller.username} est terminée avec succès',
        type='transaction_update',
        message=confirmation_message
    )
    
    print(f'   ✅ Message de confirmation envoyé')
    print(f'   🔔 Notification envoyée à l\'acheteur')
    
    # Étape 4: Message final
    final_message = Message.objects.create(
        chat=chat,
        sender=buyer,
        content='Parfait ! J\'ai bien reçu les informations. Merci pour la transaction !',
        message_type='text'
    )
    
    print(f'   ✅ Message final envoyé')
    
    # Statistiques finales
    print(f'\n📊 Statistiques finales:')
    total_messages = Message.objects.filter(chat=chat).count()
    total_notifications = Notification.objects.filter(
        user__in=[buyer, seller]
    ).count()
    
    print(f'   💬 Total des messages: {total_messages}')
    print(f'   🔔 Total des notifications: {total_notifications}')
    print(f'   ✅ Transaction: {transaction.get_status_display()}')
    print(f'   🔓 Chat: {"Débloqué" if not chat.is_locked else "Bloqué"}')
    
    print(f'\n🎉 Processus de paiement simulé avec succès !')
    print(f'🔗 URL du chat: http://localhost:8000/chat/transaction/{transaction.id}/')
    
    # Instructions pour tester
    print(f'\n💡 Instructions pour tester:')
    print(f'   1. Démarrer le serveur: python start_chat_server.py')
    print(f'   2. Se connecter avec ftr1: http://localhost:8000/')
    print(f'   3. Aller sur: http://localhost:8000/chat/list/')
    print(f'   4. Ouvrir le chat de transaction')
    print(f'   5. Vérifier que le chat est maintenant débloqué')

if __name__ == '__main__':
    simulate_payment_process()
