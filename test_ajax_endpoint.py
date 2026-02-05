#!/usr/bin/env python
"""
Script de test pour vérifier l'endpoint AJAX du chat
"""
import os
import sys
import django
import requests

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Transaction, Chat, Message, Notification

def test_ajax_endpoint():
    print("🧪 Test de l'endpoint AJAX du chat")
    print("=" * 50)
    
    # Récupérer la transaction de test
    transaction = Transaction.objects.filter(status='processing').first()
    if not transaction:
        print("❌ Aucune transaction en mode processing trouvée")
        return
    
    print(f"✅ Transaction: {transaction.id}")
    print(f"✅ Statut: {transaction.get_status_display()}")
    
    # Vérifier le chat
    try:
        chat = Chat.objects.get(transaction=transaction)
        print(f"✅ Chat: {chat.id}")
        print(f"✅ Chat actif: {chat.is_active}")
        print(f"✅ Chat bloqué: {chat.is_locked}")
    except Chat.DoesNotExist:
        print("❌ Chat non trouvé")
        return
    
    # Tester l'endpoint AJAX
    print(f"\n📝 Test de l'endpoint AJAX...")
    
    # URL de l'endpoint
    url = f"http://localhost:8000/chat/{chat.id}/send/"
    print(f"🔗 URL: {url}")
    
    # Données de test
    data = {
        'content': 'Test message via AJAX',
        'message_type': 'text'
    }
    
    # Headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        # Faire la requête POST
        response = requests.post(url, data=data, headers=headers, timeout=10)
        
        print(f"📊 Statut de la réponse: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"✅ Réponse JSON: {json_response}")
                
                if json_response.get('status') == 'success':
                    print("✅ Message envoyé avec succès via AJAX")
                else:
                    print(f"⚠️ Réponse inattendue: {json_response}")
            except ValueError:
                print(f"⚠️ Réponse non-JSON: {response.text}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"❌ Contenu de l'erreur: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion - Le serveur n'est pas démarré")
        print("💡 Démarrez le serveur avec: python manage.py runserver")
    except requests.exceptions.Timeout:
        print("❌ Timeout - La requête a pris trop de temps")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
    
    # Vérifier les messages dans la base de données
    messages = Message.objects.filter(chat=chat)
    print(f"\n📊 Messages dans la base de données: {messages.count()}")
    
    for message in messages:
        print(f"   - {message.sender.username}: {message.content[:30]}...")
    
    print(f"\n✅ Test terminé !")
    print(f"💡 Instructions pour tester manuellement:")
    print(f"   1. Démarrer le serveur: python manage.py runserver")
    print(f"   2. Aller sur: http://localhost:8000/transaction/{transaction.id}/")
    print(f"   3. Ouvrir la console du navigateur (F12)")
    print(f"   4. Tester l'envoi de messages")
    print(f"   5. Vérifier que les messages s'affichent")

if __name__ == '__main__':
    test_ajax_endpoint()
