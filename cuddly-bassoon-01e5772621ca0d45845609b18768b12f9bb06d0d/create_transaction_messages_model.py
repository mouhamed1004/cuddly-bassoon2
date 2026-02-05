#!/usr/bin/env python
"""
Script pour créer un modèle de messages spécifiques aux transactions
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.db import models
from django.contrib.auth.models import User
from blizzgame.models import Transaction
import uuid

# Créer le modèle TransactionMessage
class TransactionMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='transaction_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Transaction message from {self.sender.username} at {self.created_at}"

print("✅ Modèle TransactionMessage créé")
print("📝 Pour l'utiliser, ajoutez ce code dans blizzgame/models.py:")
print("""
class TransactionMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='transaction_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Transaction message from {self.sender.username} at {self.created_at}"
""")
