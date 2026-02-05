#!/usr/bin/env python
import requests
import json

def test_homepage():
    """Tester la page d'accueil pour voir s'il y a des messages d'erreur"""
    
    base_url = "http://localhost:8000"
    
    print("=== Test de la page d'accueil ===")
    
    try:
        response = requests.get(f"{base_url}/", allow_redirects=True)
        print(f"Status Code: {response.status_code}")
        print(f"URL finale: {response.url}")
        
        # Vérifier s'il y a des messages d'erreur dans le contenu
        content = response.text
        if "Une erreur est survenue lors du traitement de votre paiement" in content:
            print("❌ MESSAGE D'ERREUR DÉTECTÉ sur la page d'accueil!")
        else:
            print("✓ Aucun message d'erreur détecté sur la page d'accueil")
            
        # Vérifier s'il y a des messages Django
        if "messages" in content.lower() or "alert" in content.lower():
            print("ℹ️ Messages ou alertes détectés dans le contenu")
            
        # Chercher des messages spécifiques
        if "erreur" in content.lower():
            print("⚠️ Le mot 'erreur' est présent dans le contenu")
            
        if "paiement" in content.lower():
            print("ℹ️ Le mot 'paiement' est présent dans le contenu")
            
    except Exception as e:
        print(f"Erreur lors du test de la page d'accueil: {e}")

if __name__ == "__main__":
    test_homepage()

