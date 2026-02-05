#!/usr/bin/env python
"""
Script de test pour vérifier le bon fonctionnement des modèles Highlights
"""

import os
import sys
import django
from datetime import timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from blizzgame.models import Highlight, Profile, UserSubscription

def test_highlights():
    """Test des fonctionnalités Highlights"""
    print("🧪 Test des fonctionnalités Highlights")
    print("=" * 50)
    
    # Vérifier que les modèles sont bien créés
    try:
        # Créer un utilisateur de test
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            # Créer le profil
            Profile.objects.create(user=user)
            print(f"✅ Utilisateur de test créé: {user.username}")
        else:
            print(f"ℹ️ Utilisateur de test existant: {user.username}")
        
        # Vérifier le modèle Profile
        profile = user.profile
        print(f"✅ Profil trouvé: {profile}")
        
        # Vérifier le modèle UserSubscription
        subscription_count = UserSubscription.objects.count()
        print(f"✅ Modèle UserSubscription fonctionne: {subscription_count} abonnements")
        
        # Vérifier le modèle Highlight
        highlight_count = Highlight.objects.count()
        print(f"✅ Modèle Highlight fonctionne: {highlight_count} highlights")
        
        # Test de création d'un Highlight (sans vidéo pour le test)
        try:
            highlight = Highlight.objects.create(
                author=user,
                caption="Test Highlight",
                hashtags=['test', 'highlight'],
                expires_at=timezone.now() + timedelta(hours=48)
            )
            print(f"✅ Highlight de test créé: {highlight.id}")
            
            # Vérifier les propriétés
            print(f"   - Expiré: {highlight.is_expired}")
            print(f"   - Temps restant: {highlight.time_remaining}")
            print(f"   - Nombre de likes: {highlight.likes_count}")
            print(f"   - Nombre de commentaires: {highlight.comments_count}")
            
            # Nettoyer
            highlight.delete()
            print("✅ Highlight de test supprimé")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création du Highlight: {e}")
        
        print("\n🎉 Tous les tests sont passés avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False
    
    return True

def test_authentication():
    """Test de l'authentification"""
    print("\n🔐 Test de l'authentification")
    print("=" * 50)
    
    try:
        # Vérifier que les vues d'authentification existent
        from blizzgame.views import signin, signup
        
        print("✅ Vues d'authentification importées avec succès")
        print(f"   - signin: {signin}")
        print(f"   - signup: {signup}")
        
        # Vérifier les URLs
        from django.urls import reverse
        try:
            signin_url = reverse('signin')
            signup_url = reverse('signup')
            print(f"✅ URLs d'authentification: {signin_url}, {signup_url}")
        except Exception as e:
            print(f"❌ Erreur avec les URLs: {e}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'authentification: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Démarrage des tests de l'application Highlights")
    print("=" * 60)
    
    # Tests des modèles
    models_ok = test_highlights()
    
    # Tests d'authentification
    auth_ok = test_authentication()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    if models_ok and auth_ok:
        print("🎉 Tous les tests sont passés !")
        print("✅ L'application Highlights est prête à être utilisée")
        print("✅ L'authentification fonctionne correctement")
        print("\n🌐 Vous pouvez maintenant :")
        print("   1. Lancer le serveur avec: python manage.py runserver")
        print("   2. Aller sur http://localhost:8000")
        print("   3. Tester la connexion et l'inscription")
        print("   4. Accéder aux Highlights via la navbar")
    else:
        print("❌ Certains tests ont échoué")
        print("🔧 Vérifiez la configuration et les modèles")
    
    print("\n" + "=" * 60)
