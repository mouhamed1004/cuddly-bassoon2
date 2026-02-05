#!/usr/bin/env python3
"""
Script pour tester les liens légaux du footer
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_legal_links():
    """Teste les liens légaux du footer"""
    print("TEST DES LIENS LEGAUX")
    print("=" * 40)
    
    try:
        client = Client()
        
        # Test 1: Conditions d'utilisation
        print("1. Test Conditions d'utilisation...")
        try:
            url = reverse('condition_utilisation')
            print(f"   URL: {url}")
            
            response = client.get(url)
            print(f"   Statut: {response.status_code}")
            
            if response.status_code == 200:
                print("   OK: Page accessible")
                content = response.content.decode()
                if 'Conditions d\'utilisation' in content:
                    print("   OK: Contenu trouvé")
                else:
                    print("   ERREUR: Contenu manquant")
            else:
                print("   ERREUR: Page non accessible")
                
        except Exception as e:
            print(f"   ERREUR: {e}")
        
        # Test 2: Politique de confidentialité
        print("\n2. Test Politique de confidentialité...")
        try:
            url = reverse('politique_confidentialite')
            print(f"   URL: {url}")
            
            response = client.get(url)
            print(f"   Statut: {response.status_code}")
            
            if response.status_code == 200:
                print("   OK: Page accessible")
                content = response.content.decode()
                if 'Politique de confidentialité' in content:
                    print("   OK: Contenu trouvé")
                else:
                    print("   ERREUR: Contenu manquant")
            else:
                print("   ERREUR: Page non accessible")
                
        except Exception as e:
            print(f"   ERREUR: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    test_legal_links()
