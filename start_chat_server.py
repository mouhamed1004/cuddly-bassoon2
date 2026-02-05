#!/usr/bin/env python
"""
Script de démarrage pour tester le serveur de chat Django Channels
"""
import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def start_django_server():
    """Démarre le serveur Django"""
    print("🚀 Démarrage du serveur Django avec Django Channels...")
    
    # Vérifier que nous sommes dans le bon répertoire
    if not Path("manage.py").exists():
        print("❌ Fichier manage.py non trouvé. Assurez-vous d'être dans le répertoire du projet.")
        return None
    
    # Démarrer le serveur Django
    try:
        process = subprocess.Popen([
            sys.executable, "manage.py", "runserver", "0.0.0.0:8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("✅ Serveur Django démarré sur http://localhost:8000")
        return process
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du serveur: {e}")
        return None

def check_server_health():
    """Vérifie que le serveur est en cours d'exécution"""
    import requests
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur Django accessible")
            return True
        else:
            print(f"⚠️ Serveur accessible mais statut: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Serveur non accessible: {e}")
        return False

def open_browser():
    """Ouvre le navigateur sur la page d'accueil"""
    print("🌐 Ouverture du navigateur...")
    try:
        webbrowser.open("http://localhost:8000/")
        print("✅ Navigateur ouvert")
    except Exception as e:
        print(f"❌ Erreur lors de l'ouverture du navigateur: {e}")

def show_chat_urls():
    """Affiche les URLs de chat disponibles"""
    print("\n📋 URLs de chat disponibles :")
    print("=" * 50)
    
    # URLs de base
    base_url = "http://localhost:8000"
    
    print(f"🏠 Page d'accueil: {base_url}/")
    print(f"💬 Liste des chats: {base_url}/chat/list/")
    
    # URLs de test (nécessitent des données de test)
    print(f"\n🧪 URLs de test (nécessitent des données de test) :")
    print(f"   Transaction chat: {base_url}/chat/transaction/<transaction_id>/")
    print(f"   Dispute chat: {base_url}/chat/dispute/<dispute_id>/")
    
    print(f"\n🔌 WebSocket URLs :")
    print(f"   Transaction WebSocket: ws://localhost:8000/ws/chat/transaction/<transaction_id>/")
    print(f"   Dispute WebSocket: ws://localhost:8000/ws/chat/dispute/<dispute_id>/")

def show_test_instructions():
    """Affiche les instructions de test"""
    print("\n📖 Instructions de test :")
    print("=" * 50)
    
    print("1. 🧪 Créer des données de test :")
    print("   python test_chat_system.py")
    
    print("\n2. 🔔 Tester les notifications :")
    print("   python test_chat_notifications.py")
    
    print("\n3. 🔗 Tester l'intégration complète :")
    print("   python test_chat_integration.py")
    
    print("\n4. 🌐 Tester l'interface utilisateur :")
    print("   - Ouvrir http://localhost:8000/")
    print("   - Se connecter avec un utilisateur de test")
    print("   - Naviguer vers /chat/list/")
    print("   - Ouvrir un chat de transaction ou de litige")
    
    print("\n5. 🔌 Tester les WebSockets :")
    print("   python test_websocket_server.py")
    
    print("\n6. 🧹 Nettoyer les données de test :")
    print("   python cleanup_test_data.py")

def create_cleanup_script():
    """Crée un script de nettoyage des données de test"""
    cleanup_script = """#!/usr/bin/env python
'''
Script de nettoyage des données de test du système de chat
'''
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Post, Transaction, Chat, Message, Dispute, Notification

def cleanup_test_data():
    print("🧹 Nettoyage des données de test du système de chat")
    print("=" * 50)
    
    # Supprimer les utilisateurs de test
    test_users = ['test_buyer_chat', 'test_seller_chat', 'test_admin_chat']
    for username in test_users:
        try:
            user = User.objects.get(username=username)
            user.delete()
            print(f"✅ Utilisateur supprimé: {username}")
        except User.DoesNotExist:
            print(f"⚠️ Utilisateur non trouvé: {username}")
    
    # Supprimer les posts de test
    test_posts = Post.objects.filter(title__contains='test pour chat')
    count = test_posts.count()
    test_posts.delete()
    print(f"✅ {count} posts de test supprimés")
    
    # Supprimer les transactions de test
    test_transactions = Transaction.objects.filter(
        buyer__username__in=test_users,
        seller__username__in=test_users
    )
    count = test_transactions.count()
    test_transactions.delete()
    print(f"✅ {count} transactions de test supprimées")
    
    # Supprimer les chats de test
    test_chats = Chat.objects.filter(
        transaction__buyer__username__in=test_users,
        transaction__seller__username__in=test_users
    )
    count = test_chats.count()
    test_chats.delete()
    print(f"✅ {count} chats de test supprimés")
    
    # Supprimer les messages de test
    test_messages = Message.objects.filter(
        sender__username__in=test_users
    )
    count = test_messages.count()
    test_messages.delete()
    print(f"✅ {count} messages de test supprimés")
    
    # Supprimer les litiges de test
    test_disputes = Dispute.objects.filter(
        opened_by__username__in=test_users
    )
    count = test_disputes.count()
    test_disputes.delete()
    print(f"✅ {count} litiges de test supprimés")
    
    # Supprimer les notifications de test
    test_notifications = Notification.objects.filter(
        user__username__in=test_users
    )
    count = test_notifications.count()
    test_notifications.delete()
    print(f"✅ {count} notifications de test supprimées")
    
    print("\\n🎉 Nettoyage terminé avec succès !")

if __name__ == '__main__':
    cleanup_test_data()
"""
    
    with open("cleanup_test_data.py", "w", encoding="utf-8") as f:
        f.write(cleanup_script)
    
    print("✅ Script de nettoyage créé: cleanup_test_data.py")

def main():
    print("🎮 Démarrage du serveur de chat Django Channels")
    print("=" * 60)
    
    # Créer le script de nettoyage
    create_cleanup_script()
    
    # Démarrer le serveur Django
    server_process = start_django_server()
    if not server_process:
        return
    
    # Attendre que le serveur démarre
    print("⏳ Attente du démarrage du serveur...")
    time.sleep(5)
    
    # Vérifier la santé du serveur
    if check_server_health():
        print("✅ Serveur opérationnel")
        
        # Afficher les URLs
        show_chat_urls()
        
        # Afficher les instructions de test
        show_test_instructions()
        
        # Ouvrir le navigateur
        open_browser()
        
        print("\n🎉 Serveur de chat démarré avec succès !")
        print("\n💡 Pour arrêter le serveur, appuyez sur Ctrl+C")
        
        try:
            # Attendre que l'utilisateur arrête le serveur
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du serveur...")
            server_process.terminate()
            server_process.wait()
            print("✅ Serveur arrêté")
    else:
        print("❌ Serveur non accessible")
        server_process.terminate()

if __name__ == '__main__':
    main()

