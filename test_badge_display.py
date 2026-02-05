#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import UserReputation

def test_badge_display():
    print("=== TEST AFFICHAGE BADGES ===\n")
    
    # Prendre le premier utilisateur
    user = User.objects.first()
    if not user:
        print("Aucun utilisateur trouve!")
        return
    
    print(f"Test pour utilisateur: {user.username}")
    
    # Créer ou récupérer la réputation
    reputation, created = UserReputation.objects.get_or_create(user=user)
    
    # Ajouter des données de test
    reputation.seller_total_transactions = 10
    reputation.seller_successful_transactions = 8
    reputation.save()
    
    # Mettre à jour la réputation
    reputation.update_reputation()
    
    print(f"Score vendeur: {reputation.seller_score}")
    
    # Tester get_seller_badge
    badge = reputation.get_seller_badge()
    print(f"Badge retourne: {badge}")
    
    if badge:
        print(f"  - Nom: {badge['name']}")
        print(f"  - Niveau: {badge['level']}")
        print(f"  - Icone: {badge['icon']}")
        print(f"  - Symbole: {badge['icon_symbol']}")
        print(f"  - Tier: {badge['tier']}")
    
    # Vérifier hasattr
    print(f"hasattr userreputation: {hasattr(user, 'userreputation')}")
    
    # Tester l'accès direct
    try:
        direct_badge = user.userreputation.get_seller_badge()
        print(f"Badge direct: {direct_badge}")
    except AttributeError as e:
        print(f"Erreur acces direct: {e}")

if __name__ == "__main__":
    test_badge_display()
