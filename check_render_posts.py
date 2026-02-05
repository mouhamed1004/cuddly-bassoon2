#!/usr/bin/env python3
"""
Script pour vérifier l'état des posts sur Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, Transaction

def check_render_posts():
    """Vérifie l'état des posts sur Render"""
    print("VERIFICATION DE L'ETAT DES POSTS SUR RENDER")
    print("=" * 50)
    
    try:
        # Vérifier le nombre total de posts
        total_posts = Post.objects.count()
        print(f"Total posts: {total_posts}")
        
        if total_posts == 0:
            print("Aucun post dans la base de données")
            return True
        
        # Vérifier la répartition
        in_transaction = Post.objects.filter(is_in_transaction=True).count()
        sold = Post.objects.filter(is_sold=True).count()
        on_sale = Post.objects.filter(is_on_sale=True, is_sold=False, is_in_transaction=False).count()
        
        print(f"En transaction: {in_transaction}")
        print(f"Vendues: {sold}")
        print(f"En vente: {on_sale}")
        
        # Vérifier les premiers posts
        print("\nPremiers posts:")
        posts = Post.objects.all()[:5]
        for post in posts:
            print(f"- {post.title} ({post.game_type}) - {post.price}€ - Statut: ", end="")
            if post.is_in_transaction:
                print("En transaction")
            elif post.is_sold:
                print("Vendu")
            else:
                print("En vente")
        
        # Vérifier si ce sont des posts fictifs
        fake_posts = 0
        for post in posts:
            if hasattr(post, '_is_fake_demo') and post._is_fake_demo:
                fake_posts += 1
        
        if fake_posts > 0:
            print(f"\nPosts fictifs détectés: {fake_posts}")
        else:
            print("\nAucun post fictif détecté - ce sont des anciens posts")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    check_render_posts()
