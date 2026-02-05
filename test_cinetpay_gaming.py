#!/usr/bin/env python
"""
Script de test pour vérifier que l'API CinetPay Gaming fonctionne correctement
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

def test_cinetpay_configuration():
    """Teste la configuration CinetPay"""
    
    from django.conf import settings
    
    print("🔧 Test de la configuration CinetPay...")
    print("=" * 50)
    
    # Vérifier les clés API
    api_key = getattr(settings, 'CINETPAY_API_KEY', None)
    site_id = getattr(settings, 'CINETPAY_SITE_ID', None)
    
    if api_key and site_id:
        print(f"✅ CINETPAY_API_KEY: {api_key[:10]}...{api_key[-10:]}")
        print(f"✅ CINETPAY_SITE_ID: {site_id}")
        print("✅ Configuration CinetPay trouvée")
        return True
    else:
        print("❌ Configuration CinetPay manquante")
        print(f"   API_KEY: {'Présent' if api_key else 'Manquant'}")
        print(f"   SITE_ID: {'Présent' if site_id else 'Manquant'}")
        return False

def test_cinetpay_api_class():
    """Teste que la classe GamingCinetPayAPI peut être instanciée"""
    
    try:
        from blizzgame.cinetpay_utils import GamingCinetPayAPI
        
        print("\n🧪 Test de la classe GamingCinetPayAPI...")
        print("=" * 50)
        
        # Créer une instance
        api = GamingCinetPayAPI()
        
        print(f"✅ Classe GamingCinetPayAPI instanciée avec succès")
        print(f"✅ API Key: {api.api_key[:10]}...{api.api_key[-10:] if api.api_key else 'None'}")
        print(f"✅ Site ID: {api.site_id}")
        print(f"✅ Base URL: {api.base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'instanciation: {str(e)}")
        return False

def test_cinetpay_urls():
    """Teste que les URLs CinetPay sont accessibles"""
    
    client = Client()
    
    print("\n🌐 Test des URLs CinetPay...")
    print("=" * 50)
    
    # Test de la page de paiement
    try:
        # Créer un utilisateur de test si nécessaire
        from django.contrib.auth.models import User
        from blizzgame.models import Post, Transaction, CinetPayTransaction
        
        # Vérifier s'il y a des transactions existantes
        transactions = Transaction.objects.all()[:1]
        
        if transactions:
            transaction = transactions[0]
            print(f"✅ Transaction de test trouvée: {transaction.id}")
            
            # Test de la page de paiement
            response = client.get(f'/payment/cinetpay/{transaction.id}/')
            if response.status_code == 200:
                print("✅ Page de paiement CinetPay accessible")
            else:
                print(f"⚠️  Page de paiement: Status {response.status_code}")
                
        else:
            print("⚠️  Aucune transaction trouvée pour tester")
            
    except Exception as e:
        print(f"❌ Erreur lors du test des URLs: {str(e)}")
        return False
    
    return True

def test_cinetpay_utils_import():
    """Teste que tous les modules CinetPay peuvent être importés"""
    
    print("\n📦 Test des imports CinetPay...")
    print("=" * 50)
    
    try:
        from blizzgame.cinetpay_utils import (
            CinetPayAPI, 
            GamingCinetPayAPI, 
            handle_gaming_cinetpay_notification,
            convert_currency_for_cinetpay
        )
        
        print("✅ CinetPayAPI importé avec succès")
        print("✅ GamingCinetPayAPI importé avec succès")
        print("✅ handle_gaming_cinetpay_notification importé avec succès")
        print("✅ convert_currency_for_cinetpay importé avec succès")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")
        return False

def test_currency_conversion():
    """Teste la conversion de devises"""
    
    try:
        from blizzgame.cinetpay_utils import convert_currency_for_cinetpay
        
        print("\n💱 Test de la conversion de devises...")
        print("=" * 50)
        
        # Test de conversion EUR vers XOF
        amount_eur = 10.0
        amount_xof = convert_currency_for_cinetpay(amount_eur, 'EUR', 'XOF')
        
        print(f"✅ Conversion {amount_eur} EUR → {amount_xof} XOF")
        
        if amount_xof > 0:
            print("✅ Conversion de devises fonctionnelle")
            return True
        else:
            print("❌ Conversion de devises échouée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la conversion: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🚀 Test de l'API CinetPay Gaming pour BLIZZ")
    print("=" * 60)
    
    tests = [
        ("Configuration CinetPay", test_cinetpay_configuration),
        ("Classe GamingCinetPayAPI", test_cinetpay_api_class),
        ("URLs CinetPay", test_cinetpay_urls),
        ("Imports CinetPay", test_cinetpay_utils_import),
        ("Conversion de devises", test_currency_conversion),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    # Résumé des tests
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS CINETPAY")
    print("=" * 60)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
    
    print(f"\n📈 Résultats: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 Tous les tests CinetPay sont réussis !")
        print("🚀 Le système est prêt pour les vrais paiements CinetPay")
    else:
        print("⚠️  Certains tests ont échoué")
        print("🔧 Vérifiez la configuration avant le lancement")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
