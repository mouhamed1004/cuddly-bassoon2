#!/usr/bin/env python
"""
Script pour configurer ngrok pour les webhooks CinetPay
"""

import os
import subprocess
import time
import requests
import json

def check_ngrok_installed():
    """Vérifie si ngrok est installé"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ngrok installé: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ngrok non trouvé")
            return False
    except FileNotFoundError:
        print("❌ Ngrok non installé")
        return False

def start_ngrok_tunnel():
    """Démarre un tunnel ngrok sur le port 8000"""
    try:
        # Démarrer ngrok en arrière-plan
        process = subprocess.Popen(
            ['ngrok', 'http', '8000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("🚀 Démarrage du tunnel ngrok...")
        time.sleep(3)  # Attendre que ngrok se lance
        
        # Récupérer l'URL publique
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            tunnels = response.json()
            
            if tunnels.get('tunnels'):
                public_url = tunnels['tunnels'][0]['public_url']
                print(f"✅ Tunnel ngrok actif: {public_url}")
                return public_url, process
            else:
                print("❌ Aucun tunnel trouvé")
                return None, process
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de récupérer l'URL ngrok")
            return None, process
            
    except Exception as e:
        print(f"❌ Erreur lors du démarrage de ngrok: {e}")
        return None, None

def update_base_url_in_env(ngrok_url):
    """Met à jour la BASE_URL dans les variables d'environnement"""
    env_file = '.env'
    
    # Lire le fichier .env existant
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    # Mettre à jour BASE_URL
    env_vars['BASE_URL'] = ngrok_url
    
    # Réécrire le fichier .env
    with open(env_file, 'w') as f:
        f.write("# Configuration pour BLIZZ Gaming\n")
        f.write("# Généré automatiquement par setup_ngrok_for_cinetpay.py\n\n")
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ BASE_URL mise à jour dans .env: {ngrok_url}")

def main():
    print("🔧 Configuration Ngrok pour CinetPay Webhooks")
    print("=" * 50)
    
    # Vérifier si ngrok est installé
    if not check_ngrok_installed():
        print("\n📥 Installation de ngrok requise:")
        print("1. Téléchargez ngrok: https://ngrok.com/download")
        print("2. Extrayez l'exécutable dans votre PATH")
        print("3. Créez un compte gratuit sur https://ngrok.com/")
        print("4. Configurez votre token: ngrok authtoken YOUR_TOKEN")
        return
    
    # Démarrer le tunnel
    ngrok_url, process = start_ngrok_tunnel()
    
    if ngrok_url:
        # Mettre à jour la configuration
        update_base_url_in_env(ngrok_url)
        
        print(f"\n🎯 Configuration terminée!")
        print(f"URL publique: {ngrok_url}")
        print(f"URL des webhooks: {ngrok_url}/shop/payment/cinetpay/notification/")
        print("\n📋 Prochaines étapes:")
        print("1. Redémarrez votre serveur Django")
        print("2. Testez un paiement")
        print("3. Vérifiez les logs pour les notifications")
        print("\n⚠️  Gardez ce terminal ouvert pour maintenir le tunnel ngrok actif")
        
        # Garder le script en vie
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du tunnel ngrok...")
            if process:
                process.terminate()
    else:
        print("❌ Impossible de configurer le tunnel ngrok")

if __name__ == "__main__":
    main()
