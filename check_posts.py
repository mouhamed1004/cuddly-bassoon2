#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post

def check_posts():
    """Vérifier tous les posts pour identifier celui avec Fortnite/Niveau 100"""
    
    posts = Post.objects.all()
    print(f"Total posts: {posts.count()}")
    print("\nTous les posts:")
    
    for post in posts:
        author_name = post.author.username if post.author else "None"
        print(f"- {post.title}")
        print(f"  Author: {author_name}")
        print(f"  Sold: {post.is_sold}")
        print(f"  In Transaction: {post.is_in_transaction}")
        print(f"  On Sale: {post.is_on_sale}")
        print()
        
        # Chercher spécifiquement Fortnite ou niveau 100
        if 'fortnite' in post.title.lower() or 'niveau 100' in post.title.lower():
            print(f"*** FOUND FORTNITE/NIVEAU 100: {post.title} ***")
            print(f"    States: sold={post.is_sold}, transaction={post.is_in_transaction}, on_sale={post.is_on_sale}")

if __name__ == '__main__':
    check_posts()
