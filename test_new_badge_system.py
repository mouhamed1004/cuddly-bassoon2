#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.badge_config import get_seller_badge

def test_new_12_level_badge_system():
    """Test du nouveau système de badges à 12 niveaux"""
    
    print("=== NOUVEAU SYSTÈME DE BADGES À 12 NIVEAUX ===\n")
    print("| Score | Badge Obtenu      | Tier | Facteur | Couleur   | Icône                              |")
    print("|-------|-------------------|------|---------|-----------|-----------------------------------|")
    
    # Test avec différents scores
    test_scores = [0, 10, 20, 35, 50, 60, 68, 72, 78, 83, 88, 92, 96, 98]
    
    for score in test_scores:
        badge = get_seller_badge(score)
        if badge:
            print(f"| {score:5} | {badge['name']:17} | {badge['tier']:4} | {badge['factor']:7.2f} | {badge['color']:9} | {badge['icon']:33} |")
        else:
            print(f"| {score:5} | Aucun badge       |   -  |    -    |     -     | -                                 |")
    
    print(f"\n=== ANALYSE DU SYSTEME ===")
    print("NOUVEAUX NIVEAUX:")
    print("   - Bronze I-III : 0-44 points (facteur 1.0)")
    print("   - Argent I-III : 45-69 points (facteurs 0.9-0.7)")
    print("   - Or I-III : 70-84 points (facteurs 0.75-0.85)")
    print("   - Diamant I-III : 85-95+ points (facteurs 0.9-0.84)")
    
    print(f"\nPROGRESSION PLUS GRANULAIRE:")
    print("   - 12 niveaux au lieu de 4")
    print("   - Ecarts de 5-15 points entre niveaux")
    print("   - Facteurs de ponderation ajustes")
    
    print(f"\nNOUVELLES ICONES:")
    print("   - Chaque niveau a son insigne unique")
    print("   - Organisees par dossier (bronze/, argent/, or/, diamant/)")
    print("   - Emojis de fallback mis a jour")

if __name__ == "__main__":
    test_new_12_level_badge_system()
