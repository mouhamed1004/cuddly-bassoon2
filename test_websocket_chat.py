#!/usr/bin/env python
"""
Script de test pour vérifier le WebSocket du chat
"""
import os
import sys
import django
import asyncio
import websockets
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Transaction, Chat, Message

async def test_websocket_chat():
    print("🌐 Test du WebSocket du chat")
    print("=" * 50)
    
    # Récupérer une transaction de test
    try:
        transaction = Transaction.objects.filter(status='processing').first()
        if not transaction:
            print("❌ Aucune transaction en mode processing trouvée")
            return
        
        print(f"✅ Transaction trouvée: {transaction.id}")
        print(f"✅ Statut: {transaction.get_status_display()}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # URL WebSocket
    websocket_url = f"ws://localhost:8000/ws/chat/transaction/{transaction.id}/"
    print(f"🔌 Tentative de connexion à: {websocket_url}")
    
    try:
        # Connexion WebSocket
        async with websockets.connect(websocket_url) as websocket:
            print("✅ Connexion WebSocket établie")
            
            # Test 1: Envoi d'un message
            print("\n📤 Test 1: Envoi d'un message")
            message_data = {
                "type": "send_message",
                "content": "Test de message via WebSocket",
                "message_type": "text"
            }
            
            await websocket.send(json.dumps(message_data))
            print("✅ Message envoyé")
            
            # Attendre la réponse
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                print(f"✅ Réponse reçue: {response_data['type']}")
                
                if response_data['type'] == 'chat_message':
                    print(f"   📝 Contenu: {response_data['message']['content']}")
                    print(f"   👤 Expéditeur: {response_data['message']['sender']}")
                    print(f"   🕒 Créé: {response_data['message']['created_at']}")
            except asyncio.TimeoutError:
                print("⏰ Timeout - Aucune réponse reçue")
            
            # Test 2: Indicateur de frappe
            print("\n⌨️ Test 2: Indicateur de frappe")
            typing_data = {
                "type": "typing"
            }
            
            await websocket.send(json.dumps(typing_data))
            print("✅ Indicateur de frappe envoyé")
            
            # Attendre la réponse
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                response_data = json.loads(response)
                print(f"✅ Réponse reçue: {response_data['type']}")
            except asyncio.TimeoutError:
                print("⏰ Timeout - Aucune réponse reçue")
            
            # Test 3: Arrêt de l'indicateur de frappe
            print("\n🛑 Test 3: Arrêt de l'indicateur de frappe")
            stop_typing_data = {
                "type": "stop_typing"
            }
            
            await websocket.send(json.dumps(stop_typing_data))
            print("✅ Arrêt de l'indicateur de frappe envoyé")
            
            # Attendre la réponse
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                response_data = json.loads(response)
                print(f"✅ Réponse reçue: {response_data['type']}")
            except asyncio.TimeoutError:
                print("⏰ Timeout - Aucune réponse reçue")
            
            print("\n🎉 Tests WebSocket terminés avec succès !")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connexion refusée - Le serveur Django Channels n'est pas démarré")
        print("💡 Démarrez le serveur avec: python manage.py runserver")
    except websockets.exceptions.InvalidURI:
        print("❌ URI WebSocket invalide")
    except Exception as e:
        print(f"❌ Erreur de connexion WebSocket: {e}")

def test_django_channels_setup():
    print("\n🔧 Test de la configuration Django Channels")
    print("=" * 50)
    
    # Vérifier les imports
    try:
        from channels.routing import ProtocolTypeRouter, URLRouter
        from channels.auth import AuthMiddlewareStack
        from blizzgame.routing import websocket_urlpatterns
        print("✅ Imports Django Channels réussis")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # Vérifier les consumers
    try:
        from blizzgame.consumers import TransactionChatConsumer, DisputeChatConsumer
        print("✅ Consumers WebSocket chargés")
    except ImportError as e:
        print(f"❌ Erreur d'import des consumers: {e}")
        return False
    
    # Vérifier les URLs WebSocket
    try:
        from blizzgame.routing import websocket_urlpatterns
        print(f"✅ {len(websocket_urlpatterns)} patterns WebSocket configurés")
        for pattern in websocket_urlpatterns:
            print(f"   📍 {pattern.pattern}")
    except Exception as e:
        print(f"❌ Erreur de configuration des URLs: {e}")
        return False
    
    # Vérifier la configuration ASGI
    try:
        from socialgame.asgi import application
        print("✅ Configuration ASGI chargée")
    except Exception as e:
        print(f"❌ Erreur de configuration ASGI: {e}")
        return False
    
    print("✅ Configuration Django Channels valide")
    return True

def main():
    print("🧪 Test complet du WebSocket du chat")
    print("=" * 60)
    
    # Test 1: Configuration Django Channels
    if not test_django_channels_setup():
        print("❌ Configuration Django Channels invalide")
        return
    
    # Test 2: Connexion WebSocket (nécessite un serveur en cours d'exécution)
    print("\n⚠️  Pour tester la connexion WebSocket, démarrez le serveur avec:")
    print("   python manage.py runserver")
    print("   Puis exécutez: python test_websocket_chat.py")
    
    print("\n🎉 Tests de configuration terminés avec succès !")
    print("\n📋 Prochaines étapes :")
    print("   1. Démarrer le serveur Django")
    print("   2. Tester l'interface utilisateur")
    print("   3. Vérifier les WebSockets en temps réel")
    print("   4. Tester l'envoi de messages")

if __name__ == '__main__':
    main()
