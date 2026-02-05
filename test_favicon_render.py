#!/usr/bin/env python3
"""
Script pour tester la favicon sur Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client

def test_favicon_render():
    """Teste la favicon sur Render"""
    print("TEST FAVICON RENDER")
    print("=" * 40)
    
    try:
        client = Client()
        
        # Test 1: Vérifier l'accessibilité de l'image
        print("1. Test accessibilite de l'image...")
        response = client.get('/static/icon.png')
        print(f"   Statut: {response.status_code}")
        
        if response.status_code == 200:
            print("   OK: Image accessible")
            # Vérifier le type de contenu
            content_type = response.get('Content-Type', '')
            print(f"   Content-Type: {content_type}")
        else:
            print("   ERREUR: Image non accessible")
        
        # Test 2: Vérifier le contenu HTML
        print("\n2. Test contenu HTML...")
        response = client.get('/')
        print(f"   Statut: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode()
            
            # Chercher les balises favicon
            favicon_lines = [line.strip() for line in content.split('\n') if 'icon.png' in line]
            print(f"   Lignes avec icon.png: {len(favicon_lines)}")
            
            for i, line in enumerate(favicon_lines):
                print(f"   Ligne {i+1}: {line}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    test_favicon_render()
