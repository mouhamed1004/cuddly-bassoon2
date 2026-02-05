#!/usr/bin/env python
"""
Script pour reconfigurer rapidement les webhooks avec une nouvelle URL
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.core.management import call_command

def main():
    print("RECONFIGURATION RAPIDE DES WEBHOOKS")
    print("=" * 50)
    
    # Demander la nouvelle URL
    new_url = input("Entrez votre nouvelle URL Cloudflare (ex: https://nouvelle-url.trycloudflare.com): ").strip()
    
    if not new_url:
        print("URL requise")
        return False
    
    if not new_url.startswith('http'):
        new_url = 'https://' + new_url
    
    print(f"Reconfiguration avec: {new_url}")
    
    try:
        # Reconfigurer les webhooks
        call_command('setup_shopify_webhooks', '--base-url', new_url, '--force')
        print("Webhooks reconfigures avec succes!")
        
        # Tester la configuration
        call_command('monitor_shopify_sync', '--check-webhooks')
        
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nWebhooks reconfigures! Testez maintenant en modifiant un prix sur Shopify.")
    else:
        print("\nEchec de la reconfiguration.")
