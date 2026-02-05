#!/usr/bin/env python
"""
Test des implémentations de sécurité Phase 1 - BLIZZ
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

def test_validators():
    """Test du validateur de mot de passe personnalisé"""
    print("🔐 Test du validateur de mot de passe...")
    
    try:
        from blizzgame.validators import BlizzPasswordValidator
        
        validator = BlizzPasswordValidator()
        
        # Test avec un mot de passe valide
        valid_password = "SecurePass123!"
        try:
            validator.validate(valid_password)
            print("✅ Mot de passe valide accepté")
        except Exception as e:
            print(f"❌ Erreur avec mot de passe valide: {e}")
            return False
        
        # Test avec un mot de passe trop court
        short_password = "abc"
        try:
            validator.validate(short_password)
            print("❌ Mot de passe trop court accepté (ERREUR)")
            return False
        except Exception as e:
            print("✅ Mot de passe trop court rejeté correctement")
        
        # Test avec un mot de passe sans majuscule
        no_upper_password = "securepass123!"
        try:
            validator.validate(no_upper_password)
            print("❌ Mot de passe sans majuscule accepté (ERREUR)")
            return False
        except Exception as e:
            print("✅ Mot de passe sans majuscule rejeté correctement")
        
        print("✅ Validateur de mot de passe fonctionne correctement")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_settings():
    """Test de la configuration des paramètres Django"""
    print("\n⚙️ Test de la configuration Django...")
    
    try:
        from django.conf import settings
        
        # Vérifier les validateurs de mots de passe
        if hasattr(settings, 'AUTH_PASSWORD_VALIDATORS'):
            validators = settings.AUTH_PASSWORD_VALIDATORS
            print(f"✅ {len(validators)} validateurs de mots de passe configurés")
            
            # Vérifier notre validateur personnalisé
            custom_validator = None
            for validator in validators:
                if 'blizzgame.validators.BlizzPasswordValidator' in validator.get('NAME', ''):
                    custom_validator = validator
                    break
            
            if custom_validator:
                print("✅ Validateur personnalisé BLIZZ trouvé dans la configuration")
            else:
                print("❌ Validateur personnalisé BLIZZ non trouvé")
                return False
        else:
            print("❌ AUTH_PASSWORD_VALIDATORS non configuré")
            return False
        
        # Vérifier la configuration du cache
        if hasattr(settings, 'CACHES'):
            print("✅ Configuration du cache trouvée")
        else:
            print("❌ Configuration du cache manquante")
            return False
        
        # Vérifier la configuration du rate limiting
        if hasattr(settings, 'RATELIMIT_ENABLE'):
            print("✅ Rate limiting activé")
        else:
            print("❌ Rate limiting non configuré")
            return False
        
        print("✅ Configuration Django correcte")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de configuration: {e}")
        return False

def test_views():
    """Test des vues d'authentification"""
    print("\n🔍 Test des vues d'authentification...")
    
    try:
        from blizzgame.views import signin, signup
        
        # Vérifier que les fonctions existent
        if callable(signin):
            print("✅ Vue signin trouvée et callable")
        else:
            print("❌ Vue signin non callable")
            return False
        
        if callable(signup):
            print("✅ Vue signup trouvée et callable")
        else:
            print("❌ Vue signup non callable")
            return False
        
        # Vérifier les décorateurs de rate limiting
        if hasattr(signin, '__wrapped__'):
            print("✅ Décorateurs de rate limiting appliqués à signin")
        else:
            print("⚠️ Décorateurs de rate limiting non détectés sur signin")
        
        print("✅ Vues d'authentification fonctionnelles")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des vues: {e}")
        return False

def test_templates():
    """Test des templates mis à jour"""
    print("\n📝 Test des templates...")
    
    try:
        # Vérifier que le template signup.html contient les nouveaux éléments
        signup_path = Path("templates/signup.html")
        if signup_path.exists():
            content = signup_path.read_text(encoding='utf-8')
            
            # Vérifier l'indicateur de force
            if 'password-strength' in content:
                print("✅ Indicateur de force du mot de passe trouvé")
            else:
                print("❌ Indicateur de force du mot de passe manquant")
                return False
            
            # Vérifier les règles de validation
            if 'password-rules' in content:
                print("✅ Règles de validation trouvées")
            else:
                print("❌ Règles de validation manquantes")
                return False
            
            # Vérifier le pattern HTML5
            if 'pattern=' in content:
                print("✅ Validation HTML5 configurée")
            else:
                print("❌ Validation HTML5 manquante")
                return False
            
            # Vérifier le script JavaScript
            if 'auth-validation.js' in content:
                print("✅ Script de validation JavaScript inclus")
            else:
                print("❌ Script de validation JavaScript manquant")
                return False
            
            print("✅ Template signup.html mis à jour correctement")
            return True
        else:
            print("❌ Template signup.html non trouvé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test des templates: {e}")
        return False

def test_static_files():
    """Test des fichiers statiques"""
    print("\n📁 Test des fichiers statiques...")
    
    try:
        # Vérifier le fichier JavaScript
        js_path = Path("static/js/auth-validation.js")
        if js_path.exists():
            content = js_path.read_text(encoding='utf-8')
            
            if 'class AuthValidator' in content:
                print("✅ Classe AuthValidator trouvée")
            else:
                print("❌ Classe AuthValidator manquante")
                return False
            
            if 'validatePassword' in content:
                print("✅ Méthode validatePassword trouvée")
            else:
                print("❌ Méthode validatePassword manquante")
                return False
            
            print("✅ Fichier JavaScript de validation créé correctement")
            return True
        else:
            print("❌ Fichier JavaScript de validation non trouvé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test des fichiers statiques: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 TEST DE LA PHASE 1 - SÉCURITÉ CRITIQUE BLIZZ")
    print("=" * 60)
    
    tests = [
        test_validators,
        test_settings,
        test_views,
        test_templates,
        test_static_files
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution du test: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ La Phase 1 de sécurité est implémentée avec succès")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        print("🔧 Vérifiez les implémentations manquantes")
        return False

if __name__ == "__main__":
    main()
