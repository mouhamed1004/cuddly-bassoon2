#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from django.template import Template, Context

def test_template_fix():
    print("=== TEST CORRECTION TEMPLATE ===")
    
    user = User.objects.get(username='vivo')
    reputation = user.userreputation
    seller_badge = reputation.get_seller_badge()
    current_score = float(reputation.seller_score)
    
    # Reproduire le calcul exact
    from blizzgame.badge_config import SELLER_BADGES
    next_badge = None
    progress_percentage = 0
    
    for badge in SELLER_BADGES:
        if current_score < badge['min_score']:
            next_badge = badge
            break
    
    if next_badge and seller_badge:
        current_min = seller_badge['min_score']
        next_min = next_badge['min_score']
        progress_in_level = current_score - current_min
        level_range = next_min - current_min
        progress_percentage = (progress_in_level / level_range) * 100 if level_range > 0 else 100
    
    reputation_summary = {
        'seller': {
            'progress_percentage': min(progress_percentage, 100)
        }
    }
    
    # Test avec stringformat
    template_stringformat = Template('<div style="width: {{ value|stringformat:".1f" }}%;"></div>')
    context_stringformat = Context({'value': progress_percentage})
    rendered_stringformat = template_stringformat.render(context_stringformat)
    
    print(f"Progress percentage: {progress_percentage}")
    print(f"Avec stringformat: {rendered_stringformat.strip()}")
    
    # Test avec conversion manuelle
    progress_str = f"{progress_percentage:.1f}".replace(',', '.')
    print(f"Conversion manuelle: width: {progress_str}%;")

if __name__ == "__main__":
    test_template_fix()
