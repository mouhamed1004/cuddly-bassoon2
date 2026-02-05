#!/usr/bin/env python
"""
Script de démarrage pour le chat avec AJAX uniquement (Django standard)
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def start_django_server():
    """Démarre le serveur Django standard"""
    print("🚀 Démarrage du serveur Django avec chat AJAX...")
    
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
        print("⚠️ Mode AJAX uniquement (WebSockets non supportés)")
        return process
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du serveur: {e}")
        return None

def main():
    print("🎮 Démarrage du serveur Django avec chat AJAX")
    print("=" * 60)
    
    # Démarrer le serveur Django
    server_process = start_django_server()
    if not server_process:
        return
    
    # Attendre que le serveur démarre
    print("⏳ Attente du démarrage du serveur...")
    time.sleep(3)
    
    print("\n✅ Serveur opérationnel !")
    print("\n📋 URLs de test :")
    print("   - Page d'accueil: http://localhost:8000/")
    print("   - Transaction test: http://localhost:8000/transaction/167853aa-f855-426b-bb3c-c1cb772deeb4/")
    
    print("\n💡 Instructions :")
    print("   1. Se connecter avec ftr1")
    print("   2. Aller sur la page de transaction")
    print("   3. Tester l'envoi de messages (via AJAX)")
    print("   4. Ouvrir la console du navigateur pour voir les logs")
    
    print("\n⚠️ Note importante :")
    print("   - WebSockets non supportés avec runserver")
    print("   - Messages envoyés via AJAX (fallback)")
    print("   - Pour les WebSockets, utilisez: python start_chat_with_websockets.py")
    
    print("\n💡 Pour arrêter le serveur, appuyez sur Ctrl+C")
    
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
        server_process.terminate()
        server_process.wait()
        print("✅ Serveur arrêté")

if __name__ == '__main__':
    main()

