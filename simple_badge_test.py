#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import UserReputation

def simple_test():
    print("=== TEST SIMPLE BADGES ===")
    
    user = User.objects.first()
    print(f"Utilisateur: {user.username}")
    
    # Créer réputation
    reputation, created = UserReputation.objects.get_or_create(user=user)
    reputation.seller_total_transactions = 10
    reputation.seller_successful_transactions = 8
    reputation.save()
    reputation.update_reputation()
    
    print(f"Score: {reputation.seller_score}")
    
    # Test badge
    badge = reputation.get_seller_badge()
    print(f"Badge existe: {badge is not None}")
    
    if badge:
        print(f"Nom: {badge.get('name', 'N/A')}")
        print(f"Niveau: {badge.get('level', 'N/A')}")
        print(f"Icone: {badge.get('icon', 'N/A')}")
    
    # Test hasattr
    print(f"hasattr userreputation: {hasattr(user, 'userreputation')}")
    
    # Test relation inverse
    try:
        rep_obj = user.userreputation
        print(f"Relation inverse OK: {rep_obj.seller_score}")
    except:
        print("Probleme relation inverse")

if __name__ == "__main__":
    simple_test()
