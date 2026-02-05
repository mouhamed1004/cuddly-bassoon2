#!/usr/bin/env python3
"""
Script pour nettoyer les transactions de test
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import ShopCinetPayTransaction

def clean_test_transactions():
    """Nettoie les transactions de test"""
    print("NETTOYAGE DES TRANSACTIONS DE TEST")
    print("=" * 50)
    
    try:
        # Supprimer toutes les transactions CinetPay de test
        test_transactions = ShopCinetPayTransaction.objects.all()
        count = test_transactions.count()
        
        print(f"Transactions à supprimer: {count}")
        
        if count > 0:
            test_transactions.delete()
            print(f"✅ {count} transactions supprimées")
        else:
            print("Aucune transaction à supprimer")
        
        # Vérification
        remaining = ShopCinetPayTransaction.objects.count()
        print(f"Transactions restantes: {remaining}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    clean_test_transactions()
