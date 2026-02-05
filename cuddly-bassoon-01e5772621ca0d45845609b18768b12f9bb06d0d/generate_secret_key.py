#!/usr/bin/env python
"""
Script pour générer une SECRET_KEY Django sécurisée
Usage: python generate_secret_key.py
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("\n" + "="*70)
    print("🔑 NOUVELLE SECRET_KEY GÉNÉRÉE")
    print("="*70)
    print(f"\n{secret_key}\n")
    print("="*70)
    print("📋 Copiez cette clé et ajoutez-la dans Railway :")
    print("   1. Allez dans Railway Dashboard")
    print("   2. Sélectionnez votre projet")
    print("   3. Onglet 'Variables'")
    print("   4. Ajoutez : SECRET_KEY = <collez la clé ci-dessus>")
    print("="*70 + "\n")
