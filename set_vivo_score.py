#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import UserReputation

def set_vivo_score():
    try:
        user = User.objects.get(username='vivo')
        print(f"Utilisateur trouve: {user.username}")
        
        # Créer ou récupérer la réputation
        reputation, created = UserReputation.objects.get_or_create(user=user)
        
        # Définir directement le score à 60
        reputation.seller_score = 60.0
        reputation.seller_total_transactions = 15
        reputation.seller_successful_transactions = 9
        reputation.save()
        
        print(f"Score final: {reputation.seller_score}")
        
        # Vérifier le badge
        badge = reputation.get_seller_badge()
        print(f"Badge: {badge['name']}")
        print(f"Niveau: {badge['tier']}")
        print(f"Seuil minimum: {badge['min_score']}")
        
    except User.DoesNotExist:
        print("Utilisateur 'vivo' non trouve!")
        # Lister les utilisateurs disponibles
        users = User.objects.all()[:10]
        print("Utilisateurs disponibles:")
        for u in users:
            print(f"  - {u.username}")

if __name__ == "__main__":
    set_vivo_score()
