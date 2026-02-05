#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post

# Chercher l'annonce Fortnite
fortnite_posts = Post.objects.filter(title__icontains='fortnite')
print(f"Posts Fortnite trouvés: {fortnite_posts.count()}")

for post in fortnite_posts:
    print(f"Titre: {post.title}")
    print(f"Author: {post.author.username if post.author else 'None'}")
    print(f"Sold: {post.is_sold}")
    print(f"In Transaction: {post.is_in_transaction}")
    print(f"On Sale: {post.is_on_sale}")
    print("---")

# Chercher aussi par niveau 100
niveau100_posts = Post.objects.filter(title__icontains='niveau 100')
print(f"\nPosts Niveau 100 trouvés: {niveau100_posts.count()}")

for post in niveau100_posts:
    print(f"Titre: {post.title}")
    print(f"Author: {post.author.username if post.author else 'None'}")
    print(f"Sold: {post.is_sold}")
    print(f"In Transaction: {post.is_in_transaction}")
    print(f"On Sale: {post.is_on_sale}")
    print("---")
