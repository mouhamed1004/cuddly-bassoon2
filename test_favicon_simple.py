#!/usr/bin/env python3
"""
Script simple pour tester la favicon
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client

def test_favicon():
    """Teste que la favicon est bien configurée"""
    print("TEST DE LA FAVICON")
    print("=" * 40)
    
    try:
        client = Client()
        
        # Test 1: Vérifier que l'image est accessible
        print("1. Test accessibilite de l'image...")
        response = client.get('/static/icon.png')
        print(f"   Statut: {response.status_code}")
        
        if response.status_code == 200:
            print("   OK: Image icon.png accessible")
            print(f"   Taille: {len(response.content)} bytes")
        else:
            print("   ERREUR: Image icon.png non accessible")
        
        # Test 2: Page d'accueil
        print("\n2. Test page d'accueil...")
        response = client.get('/')
        print(f"   Statut: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode()
            if 'icon.png' in content:
                print("   OK: Favicon trouvee dans base.html")
            else:
                print("   ERREUR: Favicon non trouvee dans base.html")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    test_favicon()
