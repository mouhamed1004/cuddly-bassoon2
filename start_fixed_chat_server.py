#!/usr/bin/env python
"""
Script de démarrage pour tester le chat avec la correction WebSocket
"""
import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def start_django_server():
    """Démarre le serveur Django avec Django Channels"""
    print("🚀 Démarrage du serveur Django avec chat corrigé...")
    
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

def show_test_urls():
    """Affiche les URLs de test disponibles"""
    print("\n📋 URLs de test disponibles :")
    print("=" * 50)
    
    # URLs de base
    base_url = "http://localhost:8000"
    
    print(f"🏠 Page d'accueil: {base_url}/")
    print(f"💬 Liste des chats: {base_url}/chat/list/")
    
    # URLs de test spécifiques
    print(f"\n🧪 URLs de test spécifiques :")
    print(f"   Transaction ftr1 (processing): {base_url}/transaction/99147c44-4f3a-4354-a228-1172bd1b4f21/")
    print(f"   Transaction ftr1 (intégration): {base_url}/transaction/c1807e0d-0bc9-47c7-8473-da5147f208de/")
    print(f"   Transaction ftr1 (chat réel): {base_url}/transaction/43256c0d-9b02-4c10-b7c4-7d960b683d83/")
    print(f"   Transaction ftr1 (correction): {base_url}/transaction/167853aa-f855-426b-bb3c-c1cb772deeb4/")
    
    print(f"\n🔌 WebSocket URLs :")
    print(f"   Transaction processing: ws://localhost:8000/ws/chat/transaction/99147c44-4f3a-4354-a228-1172bd1b4f21/")
    print(f"   Transaction intégration: ws://localhost:8000/ws/chat/transaction/c1807e0d-0bc9-47c7-8473-da5147f208de/")
    print(f"   Transaction chat réel: ws://localhost:8000/ws/chat/transaction/43256c0d-9b02-4c10-b7c4-7d960b683d83/")
    print(f"   Transaction correction: ws://localhost:8000/ws/chat/transaction/167853aa-f855-426b-bb3c-c1cb772deeb4/")

def show_test_instructions():
    """Affiche les instructions de test"""
    print("\n📖 Instructions de test :")
    print("=" * 50)
    
    print("1. 🔐 Se connecter avec ftr1 :")
    print("   - Aller sur http://localhost:8000/")
    print("   - Se connecter avec le compte ftr1")
    
    print("\n2. 🧪 Tester la transaction avec correction WebSocket :")
    print("   - Aller sur http://localhost:8000/transaction/167853aa-f855-426b-bb3c-c1cb772deeb4/")
    print("   - Vérifier que le chat est intégré dans la page de transaction")
    print("   - Vérifier que les messages de test sont affichés")
    print("   - Tester l'envoi de nouveaux messages")
    
    print("\n3. 🔍 Vérifier les corrections :")
    print("   - Plus d'erreurs 'WebSocket is already in CLOSING or CLOSED state'")
    print("   - Gestion correcte de l'état du WebSocket")
    print("   - Reconnexion automatique en cas de déconnexion")
    print("   - Fallback AJAX si WebSocket échoue")
    print("   - Nettoyage correct des connexions")
    
    print("\n4. 🐛 Débogage :")
    print("   - Ouvrir la console du navigateur (F12)")
    print("   - Vérifier les logs de débogage")
    print("   - Vérifier la connexion WebSocket")
    print("   - Tester la reconnexion automatique")
    
    print("\n5. 🧹 Nettoyer les données de test :")
    print("   - python cleanup_test_data.py")

def main():
    print("🎮 Démarrage du serveur avec chat corrigé")
    print("=" * 60)
    
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
        show_test_urls()
        
        # Afficher les instructions de test
        show_test_instructions()
        
        print("\n🎉 Serveur avec chat corrigé démarré avec succès !")
        print("\n💡 Corrections apportées :")
        print("   - Gestion correcte de l'état du WebSocket")
        print("   - Prévention des erreurs 'CLOSING or CLOSED state'")
        print("   - Reconnexion automatique en cas de déconnexion")
        print("   - Fallback AJAX si WebSocket échoue")
        print("   - Nettoyage correct des connexions")
        print("   - Gestion des erreurs améliorée")
        
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
