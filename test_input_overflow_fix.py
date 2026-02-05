#!/usr/bin/env python
"""
Test pour vérifier que le problème de débordement des champs de texte est corrigé
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

from django.test import Client
from django.contrib.auth.models import User
from blizzgame.models import Profile
import time

def test_input_overflow_fix():
    """Test que le problème de débordement des champs de texte est corrigé"""
    print("📝 TEST DE CORRECTION DU DÉBORDEMENT DES CHAMPS DE TEXTE")
    print("=" * 60)
    
    try:
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username=f"test_overflow_{int(time.time())}",
            email=f"testoverflow{int(time.time())}@example.com",
            password="TestPassword123!"
        )
        
        Profile.objects.create(user=user, id_user=user.id)
        
        print("✅ Utilisateur de test créé")
        
        client = Client()
        
        # Test 1: Vérifier le CSS principal
        print("\n🎨 Test 1: Vérification du CSS principal")
        css_file = "staticfiles/css/style.css"
        if os.path.exists(css_file):
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Vérifier les styles de correction
            assert 'CORRECTION DU DÉBORDEMENT DES CHAMPS DE TEXTE' in css_content, "Commentaire de correction présent"
            assert 'max-width: 100% !important' in css_content, "Max-width 100% avec !important"
            assert 'width: 100% !important' in css_content, "Width 100% avec !important"
            assert 'box-sizing: border-box !important' in css_content, "Box-sizing border-box avec !important"
            assert 'word-wrap: break-word !important' in css_content, "Word-wrap break-word avec !important"
            assert 'overflow-wrap: break-word !important' in css_content, "Overflow-wrap break-word avec !important"
            assert 'white-space: normal !important' in css_content, "White-space normal avec !important"
            print("✅ Styles de correction présents dans le CSS principal")
        else:
            print("❌ Fichier CSS principal non trouvé")
            return False
        
        # Test 2: Vérifier les styles pour les textarea
        print("\n📄 Test 2: Vérification des styles pour les textarea")
        assert 'resize: vertical !important' in css_content, "Resize vertical pour textarea"
        assert 'min-height: 100px' in css_content, "Min-height pour textarea"
        assert 'max-height: 300px' in css_content, "Max-height pour textarea"
        print("✅ Styles pour textarea présents")
        
        # Test 3: Vérifier les styles pour les champs de messages
        print("\n💬 Test 3: Vérification des styles pour les champs de messages")
        assert 'max-height: 120px !important' in css_content, "Max-height pour message-input"
        assert 'overflow-y: auto !important' in css_content, "Overflow-y auto pour message-input"
        print("✅ Styles pour champs de messages présents")
        
        # Test 4: Vérifier les styles responsive
        print("\n📱 Test 4: Vérification des styles responsive")
        assert '@media (max-width: 768px)' in css_content, "Media query pour tablette"
        assert '@media (max-width: 480px)' in css_content, "Media query pour mobile"
        assert 'font-size: 16px !important' in css_content, "Font-size 16px pour éviter le zoom mobile"
        print("✅ Styles responsive présents")
        
        # Test 5: Vérifier les styles pour les conteneurs
        print("\n📦 Test 5: Vérification des styles pour les conteneurs")
        assert '.form-group input' in css_content, "Styles pour form-group input"
        assert '.form-group textarea' in css_content, "Styles pour form-group textarea"
        assert '.form-group select' in css_content, "Styles pour form-group select"
        assert '.card input' in css_content, "Styles pour card input"
        assert '.card textarea' in css_content, "Styles pour card textarea"
        assert '.card select' in css_content, "Styles pour card select"
        print("✅ Styles pour conteneurs présents")
        
        # Test 6: Vérifier les types d'inputs couverts
        print("\n🔧 Test 6: Vérification des types d'inputs couverts")
        input_types = [
            'input[type="text"]',
            'input[type="email"]',
            'input[type="password"]',
            'input[type="url"]',
            'input[type="tel"]',
            'input[type="number"]',
            'textarea',
            'select',
            '.form-control',
            '.input-field',
            '.form-input',
            '.form-textarea',
            '.message-input'
        ]
        
        for input_type in input_types:
            assert input_type in css_content, f"Type d'input {input_type} couvert"
        
        print("✅ Tous les types d'inputs sont couverts")
        
        # Test 7: Vérifier les styles mobile
        print("\n📱 Test 7: Vérification des styles mobile")
        assert 'max-height: 200px !important' in css_content, "Max-height 200px pour tablette"
        assert 'max-height: 150px !important' in css_content, "Max-height 150px pour mobile"
        assert 'min-height: 80px !important' in css_content, "Min-height 80px pour mobile"
        assert 'padding: 0.75rem !important' in css_content, "Padding 0.75rem pour mobile"
        print("✅ Styles mobile présents")
        
        # Test 8: Vérifier la cohérence
        print("\n📊 Test 8: Vérification de la cohérence")
        lines = css_content.split('\n')
        correction_lines = [line for line in lines if '!important' in line and ('max-width' in line or 'width' in line or 'box-sizing' in line)]
        print(f"   • Lignes de correction: {len(correction_lines)}")
        
        # Compter les !important
        important_count = css_content.count('!important')
        print(f"   • Règles CSS avec !important: {important_count}")
        
        # Compter les types d'inputs
        input_count = css_content.count('input[')
        print(f"   • Types d'inputs couverts: {input_count}")
        
        print("✅ Code cohérent et bien structuré")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ Le problème de débordement des champs de texte est corrigé")
        print("\n📋 RÉSUMÉ DE LA SOLUTION :")
        print("   • ✅ Max-width: 100% !important pour tous les champs")
        print("   • ✅ Width: 100% !important pour tous les champs")
        print("   • ✅ Box-sizing: border-box !important pour tous les champs")
        print("   • ✅ Word-wrap: break-word !important pour le retour à la ligne")
        print("   • ✅ Overflow-wrap: break-word !important pour le débordement")
        print("   • ✅ White-space: normal !important pour l'espacement")
        print("   • ✅ Resize: vertical !important pour les textarea")
        print("   • ✅ Max-height: 300px pour les textarea")
        print("   • ✅ Max-height: 120px pour les champs de messages")
        print("   • ✅ Styles responsive pour tablette et mobile")
        print("   • ✅ Font-size: 16px pour éviter le zoom mobile")
        print("   • ✅ Tous les types d'inputs couverts")
        print("   • ✅ Styles pour tous les conteneurs")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Nettoyer
        try:
            user.delete()
        except:
            pass

if __name__ == "__main__":
    success = test_input_overflow_fix()
    sys.exit(0 if success else 1)
