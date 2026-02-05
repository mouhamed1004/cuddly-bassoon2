#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import UserReputation
from blizzgame.badge_config import SELLER_BADGES

def test_progress_calculation():
    print("=== TEST CALCUL PROGRESSION ===")
    
    user = User.objects.first()
    reputation = user.userreputation
    current_score = float(reputation.seller_score)
    current_badge = reputation.get_seller_badge()
    
    print(f"Score actuel: {current_score}")
    print(f"Badge actuel: {current_badge['name']} (min: {current_badge['min_score']})")
    
    # Trouver le badge suivant
    next_badge = None
    for badge in SELLER_BADGES:
        if current_score < badge['min_score']:
            next_badge = badge
            break
    
    if next_badge:
        print(f"Badge suivant: {next_badge['name']} (min: {next_badge['min_score']})")
        
        current_min = current_badge['min_score']
        next_min = next_badge['min_score']
        progress_in_level = current_score - current_min
        level_range = next_min - current_min
        progress_percentage = (progress_in_level / level_range) * 100
        
        print(f"Progres dans le niveau:")
        print(f"  - Score minimum actuel: {current_min}")
        print(f"  - Score minimum suivant: {next_min}")
        print(f"  - Progres dans niveau: {progress_in_level}")
        print(f"  - Plage du niveau: {level_range}")
        print(f"  - Pourcentage: {progress_percentage:.1f}%")
    else:
        print("Niveau maximum atteint!")

if __name__ == "__main__":
    test_progress_calculation()
