#!/usr/bin/env python3
"""
Script pour tester la configuration de la favicon
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_favicon():
    """Teste que la favicon est bien configurée"""
    print("🧪 TEST DE LA FAVICON")
    print("=" * 40)
    
    try:
        client = Client()
        
        # Test 1: Page d'accueil (utilise base.html)
        print("1. Test page d'accueil...")
        response = client.get('/')
        print(f"   📊 Statut: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode()
            if 'icon.png' in content:
                print("   ✅ Favicon trouvée dans base.html")
            else:
                print("   ❌ Favicon non trouvée dans base.html")
        
        # Test 2: Page de profil (utilise profile.html)
        print("\n2. Test page de profil...")
        response = client.get('/profile/test/')
        print(f"   📊 Statut: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode()
            if 'icon.png' in content:
                print("   ✅ Favicon trouvée dans profile.html")
            else:
                print("   ❌ Favicon non trouvée dans profile.html")
        
        # Test 3: Vérifier que l'image est accessible
        print("\n3. Test accessibilité de l'image...")
        response = client.get('/static/icon.png')
        print(f"   📊 Statut: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Image icon.png accessible")
            print(f"   📏 Taille: {len(response.content)} bytes")
        else:
            print("   ❌ Image icon.png non accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    test_favicon()
