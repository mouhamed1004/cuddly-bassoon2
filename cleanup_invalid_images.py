#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Profile

print('=== NETTOYAGE DES IMAGES INVALIDES ===')

# Trouver tous les profils avec des images placeholder invalides
try:
    invalid_profiles = Profile.objects.filter(
        profileimg__icontains='via.placeholder.com'
    )

    print(f'Trouvé {invalid_profiles.count()} profils avec des images placeholder invalides')

    # Nettoyer les images invalides
    for profile in invalid_profiles:
        print(f'Nettoyage profil {profile.user.username}: {profile.profileimg.name}')
        profile.profileimg = ''  # Vider le champ
        profile.save()

    # Vérifier les bannières aussi
    invalid_banners = Profile.objects.filter(
        banner__icontains='via.placeholder.com'
    )

    print(f'Trouvé {invalid_banners.count()} profils avec des bannières placeholder invalides')

    for profile in invalid_banners:
        print(f'Nettoyage bannière {profile.user.username}: {profile.banner.name}')
        profile.banner = ''  # Vider le champ
        profile.save()

    print('✅ NETTOYAGE TERMINÉ AVEC SUCCÈS')
    
except Exception as e:
    print(f'❌ ERREUR LORS DU NETTOYAGE: {e}')
    sys.exit(1)
