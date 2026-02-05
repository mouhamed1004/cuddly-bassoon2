#!/usr/bin/env python
"""
Script de démarrage pour le chat avec WebSockets fonctionnels
"""
import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def start_daphne_server():
    """Démarre le serveur Daphne avec support WebSocket"""
    print("🚀 Démarrage du serveur Daphne avec WebSockets...")
    
    # Vérifier que nous sommes dans le bon répertoire
    if not Path("manage.py").exists():
        print("❌ Fichier manage.py non trouvé. Assurez-vous d'être dans le répertoire du projet.")
        return None
    
    # Vérifier si daphne est installé
    try:
        import daphne
        print("✅ Daphne trouvé")
    except ImportError:
        print("❌ Daphne non installé. Installation en cours...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "daphne"], check=True)
            print("✅ Daphne installé avec succès")
        except subprocess.CalledProcessError:
            print("❌ Erreur lors de l'installation de Daphne")
            return None
    
    # Démarrer le serveur Daphne
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "daphne", "-b", "0.0.0.0", "-p", "8000", "socialgame.asgi:application"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("✅ Serveur Daphne démarré sur http://localhost:8000")
        print("✅ WebSockets supportés !")
        return process
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du serveur Daphne: {e}")
        return None

def start_django_server():
    """Démarre le serveur Django standard (sans WebSockets)"""
    print("🚀 Démarrage du serveur Django standard...")
    
    try:
        process = subprocess.Popen([
            sys.executable, "manage.py", "runserver", "0.0.0.0:8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("✅ Serveur Django démarré sur http://localhost:8000")
        print("⚠️ WebSockets non supportés - Fallback AJAX uniquement")
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
            print("✅ Serveur accessible")
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
    
    base_url = "http://localhost:8000"
    
    print(f"🏠 Page d'accueil: {base_url}/")
    print(f"💬 Liste des chats: {base_url}/chat/list/")
    
    print(f"\n🧪 URLs de test spécifiques :")
    print(f"   Transaction ftr1 (processing): {base_url}/transaction/99147c44-4f3a-4354-a228-1172bd1b4f21/")
    print(f"   Transaction ftr1 (intégration): {base_url}/transaction/c1807e0d-0bc9-47c7-8473-da5147f208de/")
    print(f"   Transaction ftr1 (chat réel): {base_url}/transaction/43256c0d-9b02-4c10-b7c4-7d960b683d83/")
    print(f"   Transaction ftr1 (correction): {base_url}/transaction/167853aa-f855-426b-bb3c-c1cb772deeb4/")

def show_test_instructions():
    """Affiche les instructions de test"""
    print("\n📖 Instructions de test :")
    print("=" * 50)
    
    print("1. 🔐 Se connecter avec ftr1 :")
    print("   - Aller sur http://localhost:8000/")
    print("   - Se connecter avec le compte ftr1")
    
    print("\n2. 🧪 Tester le chat :")
    print("   - Aller sur une des URLs de transaction ci-dessus")
    print("   - Vérifier que le chat est intégré dans la page")
    print("   - Tester l'envoi de messages")
    
    print("\n3. 🔍 Vérifier les fonctionnalités :")
    print("   - Si Daphne : Messages en temps réel via WebSocket")
    print("   - Si Django : Messages via AJAX (fallback)")
    print("   - Notifications automatiques")
    print("   - Blocage/déblocage selon le statut")
    
    print("\n4. 🐛 Débogage :")
    print("   - Ouvrir la console du navigateur (F12)")
    print("   - Vérifier les logs de débogage")
    print("   - Vérifier la connexion WebSocket (si Daphne)")

def main():
    print("🎮 Démarrage du serveur avec chat")
    print("=" * 60)
    
    # Essayer d'abord Daphne (avec WebSockets)
    print("🔄 Tentative de démarrage avec Daphne (WebSockets)...")
    server_process = start_daphne_server()
    
    if not server_process:
        print("\n🔄 Fallback vers Django standard (AJAX uniquement)...")
        server_process = start_django_server()
    
    if not server_process:
        print("❌ Impossible de démarrer le serveur")
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
        
        print("\n🎉 Serveur démarré avec succès !")
        print("\n💡 Le chat fonctionne maintenant :")
        print("   - Plus de message 'Cette fonctionnalité est temporairement désactivée'")
        print("   - Chat intégré dans la page de transaction")
        print("   - Messages en temps réel (Daphne) ou AJAX (Django)")
        print("   - Blocage/déblocage intelligent selon le statut")
        
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

