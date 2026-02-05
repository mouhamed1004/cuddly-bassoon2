#!/usr/bin/env python
"""
Script de test simple pour l'endpoint AJAX
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Transaction, Chat, Message, Notification

def test_simple_ajax():
    print("🧪 Test simple de l'endpoint AJAX")
    print("=" * 40)
    
    # Récupérer toutes les transactions
    transactions = Transaction.objects.all()
    print(f"📊 Transactions totales: {transactions.count()}")
    
    for transaction in transactions:
        print(f"   - {transaction.id}: {transaction.get_status_display()}")
    
    # Récupérer tous les chats
    chats = Chat.objects.all()
    print(f"📊 Chats totaux: {chats.count()}")
    
    for chat in chats:
        print(f"   - {chat.id}: Transaction {chat.transaction.id if chat.transaction else 'N/A'}")
    
    # Récupérer tous les messages
    messages = Message.objects.all()
    print(f"📊 Messages totaux: {messages.count()}")
    
    for message in messages:
        print(f"   - {message.sender.username}: {message.content[:30]}...")
    
    print(f"\n✅ Test terminé !")

if __name__ == '__main__':
    test_simple_ajax()
