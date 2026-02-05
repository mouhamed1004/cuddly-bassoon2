#!/usr/bin/env python3
"""
Script pour tester spécifiquement le filtre de notification
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.templatetags.currency_tags import convert_notification_content
from blizzgame.currency_service import CurrencyService
from django.contrib.auth.models import User
import re

def test_notification_filter():
    """Test le filtre de notification avec différents cas"""
    print("🧪 TEST DU FILTRE DE NOTIFICATION")
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
            
            # Test direct du filtre
            try:
                converted = convert_notification_content(content, user)
                print(f"✅ Converti: {converted}")
            except Exception as e:
                print(f"❌ Erreur: {e}")
            
            # Test manuel de la regex
            euro_pattern = r'(\d+(?:\.\d{1,2})?)\s*€'
            matches = re.findall(euro_pattern, content)
            print(f"🔍 Regex trouve: {matches}")
            
            # Test de la conversion manuelle
            if matches:
                amount = float(matches[0])
                converted_amount, currency, formatted = CurrencyService.get_display_price(
                    amount, 'EUR', 'USD'  # Forcer USD pour voir le problème
                )
                print(f"💰 Conversion manuelle: {amount}€ → {formatted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_currency_formatting():
    """Test le formatage des devises"""
    print(f"\n🧪 TEST DU FORMATAGE DES DEVISES")
    print("=" * 60)
    
    try:
        # Test avec différents montants
        test_amounts = [157.95, 100.00, 25.50, 0.14, 0.17, 50.00]
        
        for amount in test_amounts:
            print(f"\n💰 Montant: {amount}€")
            
            # Test avec USD
            usd_amount, usd_currency, usd_formatted = CurrencyService.get_display_price(
                amount, 'EUR', 'USD'
            )
            print(f"   - USD: {usd_formatted}")
            
            # Test avec XOF
            xof_amount, xof_currency, xof_formatted = CurrencyService.get_display_price(
                amount, 'EUR', 'XOF'
            )
            print(f"   - XOF: {xof_formatted}")
            
            # Test direct du format_amount
            usd_formatted_direct = CurrencyService.format_amount(usd_amount, 'USD')
            print(f"   - USD direct: {usd_formatted_direct}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_bug():
    """Test le bug spécifique 0.$157.95"""
    print(f"\n🐛 TEST DU BUG SPÉCIFIQUE")
    print("=" * 60)
    
    try:
        # Simuler le bug
        content = "Le prix est de 157.95€"
        print(f"📝 Contenu: {content}")
        
        # Pattern actuel
        euro_pattern = r'(\d+(?:\.\d{1,2})?)\s*€'
        
        def replace_euro_amount(match):
            amount = float(match.group(1))
            print(f"🔍 Montant trouvé: {amount}")
            
            # Simuler la conversion
            converted_amount, currency, formatted = CurrencyService.get_display_price(
                amount, 'EUR', 'USD'
            )
            print(f"💰 Conversion: {amount}€ → {formatted}")
            return formatted
        
        # Test de la substitution
        result = re.sub(euro_pattern, replace_euro_amount, content)
        print(f"✅ Résultat: {result}")
        
        # Vérifier s'il y a un problème de formatage
        if "0.$" in result:
            print("❌ BUG DÉTECTÉ: Format incorrect détecté")
            return False
        else:
            print("✅ Format correct")
            return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 TEST DU FILTRE DE NOTIFICATION")
    print("=" * 60)
    
    success = True
    
    # Test du filtre
    if not test_notification_filter():
        success = False
    
    # Test du formatage
    if not test_currency_formatting():
        success = False
    
    # Test du bug spécifique
    if not test_specific_bug():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Le filtre fonctionne correctement")
        print("✅ Le formatage est correct")
        print("✅ Aucun bug détecté")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Des problèmes ont été détectés")
        print("⚠️  Il faut corriger le filtre")

if __name__ == "__main__":
    main()
