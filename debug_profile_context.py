#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import UserReputation
from blizzgame.badge_config import SELLER_BADGES

def debug_profile_context():
    print("=== DEBUG CONTEXTE PROFILE VIVO ===")
    
    user = User.objects.get(username='vivo')
    reputation = user.userreputation
    seller_badge = reputation.get_seller_badge()
    current_score = float(reputation.seller_score)
    
    print(f"Score: {current_score}")
    print(f"Badge name: {seller_badge['name']}")
    print(f"Badge min_score: {seller_badge['min_score']}")
    
    # Reproduire exactement le calcul de la vue profile
    next_badge = None
    progress_percentage = 0
    
    for badge in SELLER_BADGES:
        if current_score < badge['min_score']:
            next_badge = badge
            break
    
    if next_badge:
        print(f"Next badge name: {next_badge['name']}")
        print(f"Next badge min_score: {next_badge['min_score']}")
    else:
        print("Next badge: None (niveau maximum)")
    
    if next_badge and seller_badge:
        current_min = seller_badge['min_score']
        next_min = next_badge['min_score']
        progress_in_level = current_score - current_min
        level_range = next_min - current_min
        progress_percentage = (progress_in_level / level_range) * 100 if level_range > 0 else 100
        print(f"Progress percentage calcule: {progress_percentage}")
    elif not next_badge:
        progress_percentage = 100
        print("Niveau maximum - progress = 100%")
    
    # Simuler le contexte template
    reputation_summary = {
        'seller': {
            'badge': seller_badge,
            'score': current_score,
            'progress_percentage': min(progress_percentage, 100),
            'next_badge': next_badge
        }
    }
    
    print(f"\nContexte envoye au template:")
    print(f"  reputation_summary.seller.progress_percentage = {reputation_summary['seller']['progress_percentage']}")
    print(f"  reputation_summary.seller.score = {reputation_summary['seller']['score']}")
    print(f"  reputation_summary.seller.next_badge = {reputation_summary['seller']['next_badge']}")

if __name__ == "__main__":
    debug_profile_context()
