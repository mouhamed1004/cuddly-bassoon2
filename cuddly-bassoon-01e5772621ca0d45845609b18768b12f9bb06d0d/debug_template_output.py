#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from django.template import Template, Context
from django.template.loader import get_template

def debug_template_output():
    print("=== DEBUG TEMPLATE OUTPUT ===")
    
    user = User.objects.get(username='vivo')
    reputation = user.userreputation
    seller_badge = reputation.get_seller_badge()
    current_score = float(reputation.seller_score)
    
    # Reproduire le calcul exact de views.py
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
    elif not next_badge:
        progress_percentage = 100
    
    reputation_summary = {
        'seller': {
            'badge': seller_badge,
            'score': current_score,
            'progress_percentage': min(progress_percentage, 100),
            'next_badge': next_badge
        }
    }
    
    print(f"Score: {current_score}")
    print(f"Progress percentage: {progress_percentage}")
    print(f"Min progress percentage: {min(progress_percentage, 100)}")
    
    # Test du template snippet
    template_content = """
    <div class="progress-fill" style="width: {{ reputation_summary.seller.progress_percentage|floatformat:1 }}%;"></div>
    """
    
    template = Template(template_content)
    context = Context({'reputation_summary': reputation_summary})
    rendered = template.render(context)
    
    print(f"\nTemplate rendu:")
    print(rendered.strip())

if __name__ == "__main__":
    debug_template_output()
