#!/usr/bin/env python3
"""
Script simple pour créer 100 fausses annonces sur Render
- 6 en transaction
- 94 vendues
"""
import os
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, User
from django.utils import timezone
from datetime import timedelta

def main():
    print("=" * 50)
    print("CREATION DE 100 FAUSSES ANNONCES")
    print("=" * 50)
    
    # Créer ou récupérer l'utilisateur fictif
    try:
        fake_user = User.objects.get(username='fake_user')
    except User.DoesNotExist:
        fake_user = User.objects.create_user(
            username='fake_user',
            email='fake@blizz.com',
            password='fake123'
        )
        print("Utilisateur fictif créé")
    
    # Données pour les annonces
    games = ['FreeFire', 'PUBG', 'COD', 'efootball', 'fc25', 'bloodstrike']
    levels = ['Diamant', 'Platine', 'Or', 'Argent', 'Légendaire', 'Niveau 50', 'Niveau 100']
    coins_types = ['UC', 'V-Bucks', 'pièces', 'gems', 'coins']
    
    posts_created = 0
    transaction_count = 0
    sold_count = 0
    
    for i in range(100):
        # Données aléatoires
        game = random.choice(games)
        level = random.choice(levels)
        coins_amount = random.randint(1000, 50000)
        coins_type = random.choice(coins_types)
        coins = f"{coins_amount} {coins_type}"
        
        title = f"Compte {game} {level} - {coins}"
        description = f"Compte de qualité avec {coins} disponibles"
        price = Decimal(str(random.randint(1000, 50000)))
        
        # Statut: 6 premières en transaction, 94 vendues
        if i < 6:
            is_sold = False
            is_on_sale = True
            is_in_transaction = True
            transaction_count += 1
        else:
            is_sold = True
            is_on_sale = False
            is_in_transaction = False
            sold_count += 1
        
        # Créer l'annonce
        Post.objects.create(
            user=fake_user.username,
            author=fake_user,
            title=title,
            banner='def_img.png',
            caption=description,
            price=price,
            email=f'compte{i}@gaming.com',
            password=f'pass{i}',
            is_sold=is_sold,
            is_verified=random.choice([True, False]),
            is_on_sale=is_on_sale,
            is_in_transaction=is_in_transaction,
            game_type=game,
            coins=coins,
            level=level,
            created_at=timezone.now() - timedelta(days=random.randint(1, 30))
        )
        
        posts_created += 1
        
        if posts_created % 20 == 0:
            print(f"Créées: {posts_created}/100")
    
    print(f"\nTERMINE!")
    print(f"Total: {posts_created}")
    print(f"En transaction: {transaction_count}")
    print(f"Vendues: {sold_count}")
    
    # Vérification
    total = Post.objects.count()
    trans = Post.objects.filter(is_in_transaction=True).count()
    sold = Post.objects.filter(is_sold=True).count()
    
    print(f"\nVérification:")
    print(f"Total en base: {total}")
    print(f"En transaction: {trans}")
    print(f"Vendues: {sold}")

if __name__ == "__main__":
    main()

