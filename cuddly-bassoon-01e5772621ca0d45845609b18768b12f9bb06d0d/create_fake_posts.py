#!/usr/bin/env python3
"""
Script pour créer 200 annonces fictives
"""
import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Post, Transaction
from django.utils import timezone

def create_fake_posts():
    """Crée 200 annonces fictives"""
    print("CREATION DE 200 ANNONCES FICTIVES")
    print("=" * 50)
    
    try:
        # Données fictives
        fake_users = [
            "GamerPro2024", "ElitePlayer", "ChampionGaming", "ProGamerX", "GameMaster99",
            "SkillPlayer", "TopGamer", "GameKing", "PlayerElite", "GamingPro",
            "SuperPlayer", "GameHero", "PlayerKing", "GamingMaster", "EliteGamer",
            "ProPlayer", "GameChampion", "PlayerPro", "GamingElite", "TopPlayer"
        ]
        
        game_types = ['FreeFire', 'PUBG', 'COD', 'efootball', 'fc25', 'bloodstrike']
        
        titles_templates = [
            "Compte {game} niveau {level} - {coins}",
            "Vente compte {game} {level} avec {coins}",
            "Compte {game} premium niveau {level}",
            "Vente rapide compte {game} {level}",
            "Compte {game} {level} - {coins} disponibles",
            "Vente compte {game} niveau {level}",
            "Compte {game} {level} avec {coins}",
            "Vente compte {game} {level} - {coins}",
            "Compte {game} niveau {level} premium",
            "Vente compte {game} {level} avec {coins}"
        ]
        
        captions = [
            "Compte en excellent état, vente rapide",
            "Vente pour urgence, prix négociable",
            "Compte bien entretenu, nombreux items",
            "Vente rapide, contactez-moi",
            "Compte premium avec beaucoup d'items",
            "Vente pour changement de jeu",
            "Compte avec de nombreux skins",
            "Vente rapide, prix intéressant",
            "Compte bien développé",
            "Vente pour urgence financière"
        ]
        
        levels = ["1", "5", "10", "15", "20", "25", "30", "35", "40", "45", "50", "60", "70", "80", "90", "100"]
        coins_amounts = ["1000", "5000", "10000", "15000", "20000", "25000", "30000", "50000", "75000", "100000"]
        
        # Créer les annonces
        posts_created = 0
        transaction_posts = 0
        sold_posts = 0
        
        print("Creation des annonces en cours...")
        
        for i in range(200):
            # Données aléatoires
            game = random.choice(game_types)
            level = random.choice(levels)
            coins = random.choice(coins_amounts)
            user = random.choice(fake_users)
            title_template = random.choice(titles_templates)
            caption = random.choice(captions)
            
            # Créer le titre
            title = title_template.format(
                game=game,
                level=level,
                coins=coins
            )
            
            # Prix aléatoire entre 5 et 500
            price = Decimal(str(random.uniform(5, 500))).quantize(Decimal('0.01'))
            
            # Date de création aléatoire (derniers 30 jours)
            days_ago = random.randint(0, 30)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            # Déterminer le statut
            status_rand = random.random()
            is_sold = False
            is_in_transaction = False
            
            if status_rand < 0.05:  # 5% en transaction (10 annonces)
                is_in_transaction = True
                transaction_posts += 1
            elif status_rand < 0.55:  # 50% vendues (100 annonces)
                is_sold = True
                sold_posts += 1
            
            # Créer l'annonce
            post = Post.objects.create(
                user=user,
                title=title,
                caption=caption,
                created_at=created_at,
                price=price,
                email=f"{user.lower()}@gmail.com",
                password="******",
                is_sold=is_sold,
                is_on_sale=not is_sold and not is_in_transaction,
                is_in_transaction=is_in_transaction,
                game_type=game,
                coins=coins,
                level=level,
                no_of_likes=random.randint(0, 50)
            )
            
            # Marquer comme annonce fictive
            post._is_fake_demo = True
            post.save()
            
            posts_created += 1
            
            if posts_created % 50 == 0:
                print(f"Annonces creees: {posts_created}/200")
        
        print(f"\nRESUME DE LA CREATION:")
        print(f"Total annonces creees: {posts_created}")
        print(f"En transaction: {transaction_posts}")
        print(f"Vendues: {sold_posts}")
        print(f"En vente: {posts_created - transaction_posts - sold_posts}")
        
        # Vérification
        total_posts = Post.objects.count()
        print(f"\nTotal annonces dans la base: {total_posts}")
        
        if total_posts >= 200:
            print("SUCCESS: 200 annonces fictives creees avec succes!")
            return True
        else:
            print("ERREUR: Nombre d'annonces insuffisant")
            return False
        
    except Exception as e:
        print(f"ERREUR lors de la creation: {e}")
        return False

if __name__ == "__main__":
    create_fake_posts()