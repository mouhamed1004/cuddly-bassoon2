#!/usr/bin/env python3
"""
Script pour déboguer les prix dans les notifications
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Notification
from blizzgame.templatetags.currency_tags import convert_notification_content
from django.contrib.auth.models import User
import re

def debug_notification_prices():
    """Débogue les prix dans les notifications"""
    print("🔍 DÉBOGAGE DES PRIX DANS LES NOTIFICATIONS")
    print("=" * 60)
    
    try:
        # Récupérer quelques notifications avec des prix
        notifications = Notification.objects.filter(
            content__icontains='€'
        ).order_by('-created_at')[:5]
        
        print(f"📊 Notifications avec prix trouvées: {notifications.count()}")
        
        for notification in notifications:
            print(f"\n📧 Notification {notification.id.hex[:8]}:")
            print(f"   - Titre: {notification.title}")
            print(f"   - Contenu original: {notification.content}")
            
            # Tester la conversion avec différents utilisateurs
            users = User.objects.all()[:3]
            for user in users:
                try:
                    converted_content = convert_notification_content(notification.content, user)
                    print(f"   - Utilisateur {user.username}: {converted_content}")
                except Exception as e:
                    print(f"   - Erreur pour {user.username}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du débogage: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regex_patterns():
    """Test les patterns regex pour les prix"""
    print(f"\n🧪 TEST DES PATTERNS REGEX")
    print("=" * 60)
    
    # Test avec différents formats de prix
    test_cases = [
        "Le prix est de 157.95€",
        "Montant: 100€",
        "Prix: 25.50€",
        "Coût: 1000€",
        "Le prix est de 0.14€",
        "Montant: 0.17€",
    ]
    
    # Pattern actuel
    euro_pattern = r'(\d+(?:\.\d{1,2})?)\s*€'
    
    print("📊 Test du pattern actuel:")
    for test_case in test_cases:
        matches = re.findall(euro_pattern, test_case)
        print(f"   - '{test_case}' → {matches}")
    
    # Test avec des prix convertis
    converted_cases = [
        "Le prix est de $157.95",
        "Montant: $100.00",
        "Prix: $25.50",
        "Coût: $1000.00",
        "Le prix est de $0.14",
        "Montant: $0.17",
    ]
    
    print(f"\n📊 Test avec des prix convertis:")
    for test_case in converted_cases:
        matches = re.findall(euro_pattern, test_case)
        print(f"   - '{test_case}' → {matches}")
    
    return True

def test_currency_conversion():
    """Test la conversion de devises"""
    print(f"\n🧪 TEST DE CONVERSION DE DEVISES")
    print("=" * 60)
    
    try:
        from blizzgame.currency_service import CurrencyService
        
        # Test avec différents montants
        test_amounts = [157.95, 100.00, 25.50, 0.14, 0.17]
        
        for amount in test_amounts:
            print(f"\n💰 Montant: {amount}€")
            
            # Conversion vers USD
            usd_amount, usd_currency, usd_formatted = CurrencyService.get_display_price(
                amount, 'EUR', 'USD'
            )
            print(f"   - USD: {usd_formatted}")
            
            # Conversion vers XOF
            xof_amount, xof_currency, xof_formatted = CurrencyService.get_display_price(
                amount, 'EUR', 'XOF'
            )
            print(f"   - XOF: {xof_formatted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 DÉBOGAGE DES PRIX DANS LES NOTIFICATIONS")
    print("=" * 60)
    
    success = True
    
    # Débogage des notifications
    if not debug_notification_prices():
        success = False
    
    # Test des patterns regex
    if not test_regex_patterns():
        success = False
    
    # Test de conversion de devises
    if not test_currency_conversion():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 DÉBOGAGE TERMINÉ !")
        print("✅ Les tests ont été exécutés avec succès")
    else:
        print("❌ CERTAINES ERREURS ONT ÉTÉ RENCONTRÉES")
        print("⚠️  Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
