#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User

# Créer le superutilisateur
username = 'admin'
email = 'admin@blizz.com'
password = 'blizz2024!'

if User.objects.filter(username=username).exists():
    print(f"L'utilisateur '{username}' existe déjà.")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superutilisateur '{username}' créé avec succès!")
    print(f"Email: {email}")
    print(f"Mot de passe: {password}")
