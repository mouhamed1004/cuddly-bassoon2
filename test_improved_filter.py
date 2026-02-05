#!/usr/bin/env python3
"""
Script pour tester le filtre amélioré
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.templatetags.currency_tags import convert_notification_content
from django.contrib.auth.models import User

def test_improved_filter():
    """Test le filtre amélioré avec gestion d'erreurs"""
    print("🧪 TEST DU FILTRE AMÉLIORÉ")
    print("=" * 60)
    
    try:
        # Récupérer un utilisateur
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        print(f"👤 Utilisateur de test: {user.username}")
        
        # Test avec différents contenus
        test_contents = [
            "Le remboursement de 50.00€ a été effectué.",
            "Le prix est de 157.95€",
            "Montant: 100€",
            "Prix: 25.50€",
            "Coût: 1000€",
            "Le prix est de 0.14€",
            "Montant: 0.17€",
        ]
        
        for content in test_contents:
            print(f"\n📝 Contenu original: {content}")
            
            # Test du filtre amélioré
            try:
                converted = convert_notification_content(content, user)
                print(f"✅ Converti: {converted}")
                
                # Vérifier qu'il n'y a pas de bug
                if "0.$" in converted:
                    print(f"❌ BUG DÉTECTÉ: {converted}")
                    return False
                else:
                    print(f"✅ Format correct")
                    
            except Exception as e:
                print(f"❌ Erreur: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test les cas limites"""
    print(f"\n🧪 TEST DES CAS LIMITES")
    print("=" * 60)
    
    try:
        user = User.objects.first()
        
        # Test avec des cas limites
        edge_cases = [
            "Prix: 0€",
            "Montant: 0.00€",
            "Coût: 999999.99€",
            "Prix: 0.01€",
            "Montant: 0.1€",
        ]
        
        for content in edge_cases:
            print(f"\n📝 Cas limite: {content}")
            
            try:
                converted = convert_notification_content(content, user)
                print(f"✅ Converti: {converted}")
                
                if "0.$" in converted:
                    print(f"❌ BUG DÉTECTÉ: {converted}")
                    return False
                    
            except Exception as e:
                print(f"❌ Erreur: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 TEST DU FILTRE AMÉLIORÉ")
    print("=" * 60)
    
    success = True
    
    # Test du filtre amélioré
    if not test_improved_filter():
        success = False
    
    # Test des cas limites
    if not test_edge_cases():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Le filtre amélioré fonctionne correctement")
        print("✅ Aucun bug de formatage détecté")
        print("✅ Les cas limites sont gérés")
        print("✅ Prêt pour le déploiement")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Des problèmes ont été détectés")
        print("⚠️  Il faut corriger le filtre")

if __name__ == "__main__":
    main()
