#!/usr/bin/env python3
"""
Script pour déployer les annonces fictives sur Render
À exécuter sur Render après le déploiement
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, Transaction
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal

def deploy_fake_posts_render():
    """Déploie les annonces fictives sur Render"""
    print("DEPLOIEMENT DES ANNONCES FICTIVES SUR RENDER")
    print("=" * 60)
    
    try:
        # Vérifier l'environnement
        environment = os.environ.get('ENVIRONMENT', 'development')
        print(f"Environnement: {environment}")
        
        # Supprimer les annonces existantes
        print("\n1. Suppression des annonces existantes...")
        existing_posts = Post.objects.count()
        print(f"Annonces existantes: {existing_posts}")
        
        if existing_posts > 0:
            # Supprimer les transactions liées
            Transaction.objects.filter(post__isnull=False).delete()
            print("Transactions supprimées")
            
            # Supprimer les annonces
            Post.objects.all().delete()
            print("Annonces supprimées")
        
        # Créer les annonces fictives
        print("\n2. Création des annonces fictives...")
        
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
                print(f"Annonces créées: {posts_created}/200")
        
        print(f"\n3. Résumé du déploiement:")
        print(f"Total annonces créées: {posts_created}")
        print(f"En transaction: {transaction_posts}")
        print(f"Vendues: {sold_posts}")
        print(f"En vente: {posts_created - transaction_posts - sold_posts}")
        
        # Vérification finale
        total_posts = Post.objects.count()
        print(f"\nTotal annonces dans la base: {total_posts}")
        
        if total_posts >= 200:
            print("SUCCESS: Déploiement des annonces fictives réussi!")
            return True
        else:
            print("ERREUR: Nombre d'annonces insuffisant")
            return False
        
    except Exception as e:
        print(f"ERREUR lors du déploiement: {e}")
        return False

if __name__ == "__main__":
    deploy_fake_posts_render()
