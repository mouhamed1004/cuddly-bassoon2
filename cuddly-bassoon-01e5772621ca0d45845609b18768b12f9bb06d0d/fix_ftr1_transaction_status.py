#!/usr/bin/env python
"""
Script pour corriger le statut de la transaction de ftr1
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Transaction, Chat

def fix_ftr1_transaction_status():
    print('🔧 Correction du statut de la transaction de ftr1')
    print('=' * 50)
    
    # Récupérer la transaction de ftr1
    transaction = Transaction.objects.get(id='17acf02c-f856-4de6-91fa-fae4d027a970')
    chat = Chat.objects.get(transaction=transaction)
    
    print(f'📊 Statut actuel: {transaction.get_status_display()}')
    print(f'🔒 Chat bloqué: {chat.is_locked}')
    
    # Changer le statut à pending (en attente de paiement)
    transaction.status = 'pending'
    transaction.save()
    
    # Mettre à jour le chat
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f'✅ Nouveau statut: {transaction.get_status_display()}')
    print(f'🔒 Chat bloqué: {chat.is_locked}')
    print(f'🧮 Devrait être bloqué: {transaction.status in ["pending", "waiting_payment"]}')
    
    print(f'\n💡 Maintenant le chat sera bloqué jusqu\'à ce que le paiement soit validé!')
    print(f'🔗 URL du chat: http://localhost:8000/chat/transaction/{transaction.id}/')
    
    # Tester la logique de déblocage
    print(f'\n🧪 Test de déblocage du chat:')
    
    # Simuler un paiement validé
    transaction.status = 'processing'
    transaction.save()
    
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f'✅ Statut après paiement: {transaction.get_status_display()}')
    print(f'🔓 Chat débloqué: {not chat.is_locked}')
    
    # Remettre en pending pour le test
    transaction.status = 'pending'
    transaction.save()
    
    chat.is_locked = transaction.status in ['pending', 'waiting_payment']
    chat.save()
    
    print(f'✅ Remis en attente de paiement: {transaction.get_status_display()}')
    print(f'🔒 Chat bloqué: {chat.is_locked}')

if __name__ == '__main__':
    fix_ftr1_transaction_status()
