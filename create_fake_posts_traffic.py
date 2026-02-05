#!/usr/bin/env python3
"""
Script pour créer 100 fausses annonces avec du trafic simulé
- 6 annonces en transaction (en cours de vente)
- 94 annonces vendues (pour montrer l'activité)
"""
import os
import sys
import django
import random
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, User
from django.utils import timezone
from datetime import timedelta

def create_fake_posts():
    """Crée 100 fausses annonces avec du trafic simulé"""
    print("=" * 60)
    print("CREATION DE 100 FAUSSES ANNONCES POUR SIMULER LE TRAFIC")
    print("=" * 60)
    
    # Données pour les annonces
    games = [
        ('FreeFire', 'FreeFire'),
        ('PUBG', 'PUBG Mobile'),
        ('COD', 'Call of Duty Mobile'),
        ('efootball', 'eFootball Mobile'),
        ('fc25', 'FC25 Mobile'),
        ('bloodstrike', 'Bloodstrike'),
    ]
    
    titles_templates = [
        "Compte {game} niveau {level} avec {coins}",
        "Compte {game} {level} - {coins} disponibles",
        "Vente compte {game} {level} - {coins}",
        "Compte {game} {level} - {coins} - Vendu rapidement",
        "Compte {game} {level} avec {coins} - Bon prix",
    ]
    
    levels = [
        "Diamant", "Platine", "Or", "Argent", "Bronze",
        "Légendaire", "Élite", "Maître", "Champion", "Pro",
        "Niveau 50", "Niveau 75", "Niveau 100", "Niveau 150",
        "Niveau 200", "Niveau 300", "Niveau 500"
    ]
    
    coins_templates = [
        "{amount} UC", "{amount} V-Bucks", "{amount} pièces", 
        "{amount} gems", "{amount} diamonds", "{amount} coins",
        "{amount} points", "{amount} crédits"
    ]
    
    descriptions = [
        "Compte de qualité supérieure avec de nombreux skins rares",
        "Compte bien entretenu, parfait pour débuter",
        "Compte avec historique de victoires impressionnant",
        "Compte premium avec tous les avantages",
        "Compte rare avec des objets exclusifs",
        "Compte de collectionneur avec skins limitées",
        "Compte professionnel",
        "Compte avec équipe complète et stratégies",
        "Compte avec statistiques exceptionnelles",
        "Compte avec récompenses spéciales"
    ]
    
    # Récupérer ou créer un utilisateur fictif
    try:
        fake_user = User.objects.get(username='fake_user')
    except User.DoesNotExist:
        fake_user = User.objects.create_user(
            username='fake_user',
            email='fake@blizz.com',
            password='fake_password_123'
        )
        print("Utilisateur fictif créé")
    
    print(f"Utilisateur fictif: {fake_user.username}")
    
    # Créer 100 annonces
    posts_created = 0
    transaction_posts = 0
    sold_posts = 0
    
    for i in range(100):
        # Choisir un jeu aléatoire
        game_code, game_name = random.choice(games)
        
        # Générer des données aléatoires
        level = random.choice(levels)
        coins_amount = random.randint(1000, 50000)
        coins_template = random.choice(coins_templates)
        coins = coins_template.format(amount=coins_amount)
        
        # Générer un titre
        title_template = random.choice(titles_templates)
        title = title_template.format(
            game=game_name,
            level=level,
            coins=coins
        )
        
        # Générer une description
        description = random.choice(descriptions)
        
        # Générer un prix (entre 1000 et 50000 FCFA)
        price = Decimal(str(random.randint(1000, 50000)))
        
        # Déterminer le statut (6 en transaction, 94 vendues)
        if i < 6:
            # 6 premières annonces en transaction
            is_sold = False
            is_on_sale = True
            is_in_transaction = True
            status = "TRANSACTION"
            transaction_posts += 1
        else:
            # 94 annonces vendues
            is_sold = True
            is_on_sale = False
            is_in_transaction = False
            status = "VENDU"
            sold_posts += 1
        
        # Créer l'annonce
        post = Post.objects.create(
            user=fake_user.username,
            author=fake_user,
            title=title,
            banner='def_img.png',  # Image par défaut
            caption=description,
            price=price,
            email=f'compte{i}@gaming.com',
            password=f'password{i}',
            is_sold=is_sold,
            is_verified=random.choice([True, False]),
            is_on_sale=is_on_sale,
            is_in_transaction=is_in_transaction,
            game_type=game_code,
            coins=coins,
            level=level,
            created_at=timezone.now() - timedelta(days=random.randint(1, 30))
        )
        
        posts_created += 1
        
        if posts_created % 20 == 0:
            print(f"Annonces créées: {posts_created}/100")
    
    print(f"\n" + "=" * 60)
    print("CREATION TERMINEE!")
    print("=" * 60)
    print(f"Total annonces créées: {posts_created}")
    print(f"En transaction: {transaction_posts}")
    print(f"Vendues: {sold_posts}")
    print(f"Utilisateur fictif: {fake_user.username}")
    
    # Vérification
    total_posts = Post.objects.count()
    transaction_count = Post.objects.filter(is_in_transaction=True).count()
    sold_count = Post.objects.filter(is_sold=True).count()
    
    print(f"\nVERIFICATION:")
    print(f"Total annonces en base: {total_posts}")
    print(f"En transaction: {transaction_count}")
    print(f"Vendues: {sold_count}")
    
    if transaction_count == 6 and sold_count >= 94:
        print("✅ SUCCES: Configuration parfaite!")
    else:
        print("⚠️ ATTENTION: Les nombres ne correspondent pas exactement")
    
    return True

if __name__ == "__main__":
    print("Démarrage de la création des fausses annonces...")
    success = create_fake_posts()
    
    if success:
        print("\n🎉 Script terminé avec succès!")
        print("Les utilisateurs verront maintenant du trafic sur la plateforme!")
    else:
        print("\n❌ Script terminé avec des erreurs")
        sys.exit(1)

