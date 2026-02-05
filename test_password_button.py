#!/usr/bin/env python
"""
Test rapide pour vérifier que le bouton de vérification du mot de passe fonctionne
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Profile
from django.test import Client
import time

def test_password_button():
    """Tester le bouton de vérification du mot de passe"""
    print("🔒 TEST DU BOUTON DE VÉRIFICATION DU MOT DE PASSE")
    print("=" * 50)
    
    # Créer un utilisateur de test
    username = f"test_button_{int(time.time())}"
    email = f"testbutton{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name="Test",
            last_name="Button"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        print(f"✅ Utilisateur créé: {username}")
        
        # Tester l'accès à la page settings
        client = Client()
        client.login(username=username, password=password)
        
        response = client.get('/settings/')
        content = response.content.decode('utf-8')
        
        # Vérifier que le bouton est présent
        assert 'verifyPasswordBtn' in content, "Le bouton de vérification doit être présent"
        assert 'Vérifier' in content, "Le texte 'Vérifier' doit être présent"
        print("✅ Bouton de vérification présent dans le HTML")
        
        # Tester la vérification avec le bon mot de passe
        response = client.post('/verify-current-password/', 
                             data=f'{{"current_password": "{password}"}}',
                             content_type='application/json')
        
        assert response.status_code == 200, "La requête doit réussir"
        data = response.json()
        assert data['success'] == True, "La vérification doit réussir"
        print("✅ Vérification du mot de passe réussie")
        
        # Tester la vérification avec un mauvais mot de passe
        response = client.post('/verify-current-password/', 
                             data='{"current_password": "WrongPassword123!"}',
                             content_type='application/json')
        
        data = response.json()
        assert data['success'] == False, "La vérification doit échouer"
        print("✅ Vérification avec mauvais mot de passe échouée correctement")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ Le bouton de vérification du mot de passe fonctionne parfaitement")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        try:
            user.delete()
        except:
            pass

if __name__ == "__main__":
    success = test_password_button()
    sys.exit(0 if success else 1)
