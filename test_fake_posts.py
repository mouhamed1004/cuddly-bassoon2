#!/usr/bin/env python3
"""
Script pour tester les annonces fictives
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post
from django.test import Client
from django.urls import reverse

def test_fake_posts():
    """Teste les annonces fictives"""
    print("TEST DES ANNONCES FICTIVES")
    print("=" * 50)
    
    try:
        # Vérifier le nombre total d'annonces
        total_posts = Post.objects.count()
        print(f"Total annonces: {total_posts}")
        
        # Vérifier la répartition
        in_transaction = Post.objects.filter(is_in_transaction=True).count()
        sold = Post.objects.filter(is_sold=True).count()
        on_sale = Post.objects.filter(is_on_sale=True, is_sold=False, is_in_transaction=False).count()
        
        print(f"En transaction: {in_transaction}")
        print(f"Vendues: {sold}")
        print(f"En vente: {on_sale}")
        
        # Test de la page d'accueil
        print("\nTest de la page d'accueil...")
        client = Client()
        response = client.get('/')
        
        if response.status_code == 200:
            print("OK: Page d'accueil accessible")
            content = response.content.decode()
            
            # Vérifier qu'il y a des annonces
            if 'character-card' in content:
                print("OK: Annonces affichées")
            else:
                print("ERREUR: Aucune annonce affichée")
                
            # Vérifier la pagination
            if 'loadMoreBtn' in content or 'Voir plus' in content:
                print("OK: Système de pagination présent")
            else:
                print("INFO: Pas de pagination (normal si moins de 12 annonces)")
                
        else:
            print(f"ERREUR: Page d'accueil non accessible (statut: {response.status_code})")
        
        # Test de quelques annonces spécifiques
        print("\nTest des annonces spécifiques...")
        posts = Post.objects.all()[:5]
        for post in posts:
            print(f"- {post.title} ({post.game_type}) - {post.price}€ - Statut: ", end="")
            if post.is_in_transaction:
                print("En transaction")
            elif post.is_sold:
                print("Vendu")
            else:
                print("En vente")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    test_fake_posts()
