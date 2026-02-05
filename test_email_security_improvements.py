#!/usr/bin/env python
"""
Script de test pour les améliorations de sécurité de vérification email
Teste l'affichage de l'email et le système de cooldown.
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import EmailVerification, Profile
from django.utils import timezone
from datetime import timedelta
import time

def create_test_user():
    """Créer un utilisateur de test"""
    username = f"test_user_{int(time.time())}"
    email = f"test{int(time.time())}@example.com"
    
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password="TestPassword123!",
            first_name="Test",
            last_name="User"
        )
        
        # Créer le profil
        Profile.objects.create(user=user, id_user=user.id)
        
        # Créer la vérification email
        verification = EmailVerification.objects.create(user=user)
        
        print(f"✅ Utilisateur créé: {username} ({email})")
        return user, verification
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        return None, None

def test_email_display():
    """Tester l'affichage de l'email"""
    print("\n🧪 TEST 1: Affichage de l'email utilisateur")
    
    user, verification = create_test_user()
    if not user:
        return False
    
    try:
        # L'email doit être accessible via user.email
        assert user.email, "L'email de l'utilisateur ne doit pas être vide"
        print(f"✅ Email affiché: {user.email}")
        
        # Vérifier que la vérification existe
        assert verification, "L'objet EmailVerification doit exister"
        assert not verification.is_verified, "L'email ne doit pas être vérifié par défaut"
        print("✅ Vérification email créée correctement")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def test_cooldown_system():
    """Tester le système de cooldown"""
    print("\n🧪 TEST 2: Système de cooldown")
    
    user, verification = create_test_user()
    if not user:
        return False
    
    try:
        # Test 1: Premier envoi (doit être autorisé)
        assert verification.can_resend_email, "Le premier envoi doit être autorisé"
        print("✅ Premier envoi autorisé")
        
        # Simuler un envoi d'email
        verification.last_email_sent = timezone.now()
        verification.save()
        
        # Test 2: Envoi immédiat (doit être refusé)
        assert not verification.can_resend_email, "L'envoi immédiat doit être refusé"
        print("✅ Envoi immédiat refusé (cooldown actif)")
        
        # Test 3: Vérifier le temps restant
        remaining = verification.time_until_next_resend
        assert remaining is not None, "Le temps restant doit être calculé"
        assert remaining.total_seconds() > 0, "Le temps restant doit être positif"
        print(f"✅ Temps restant calculé: {remaining.total_seconds():.0f} secondes")
        
        # Test 4: Simuler l'expiration du cooldown
        verification.last_email_sent = timezone.now() - timedelta(minutes=6)
        verification.save()
        
        assert verification.can_resend_email, "L'envoi doit être autorisé après expiration"
        assert verification.time_until_next_resend is None, "Aucun temps restant après expiration"
        print("✅ Envoi autorisé après expiration du cooldown")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def test_model_methods():
    """Tester les méthodes du modèle EmailVerification"""
    print("\n🧪 TEST 3: Méthodes du modèle EmailVerification")
    
    user, verification = create_test_user()
    if not user:
        return False
    
    try:
        # Test des propriétés
        assert hasattr(verification, 'can_resend_email'), "Méthode can_resend_email manquante"
        assert hasattr(verification, 'time_until_next_resend'), "Méthode time_until_next_resend manquante"
        assert hasattr(verification, 'is_expired'), "Méthode is_expired manquante"
        print("✅ Toutes les méthodes sont présentes")
        
        # Test de la méthode send_verification_email
        assert hasattr(verification, 'send_verification_email'), "Méthode send_verification_email manquante"
        print("✅ Méthode send_verification_email présente")
        
        # Test des champs
        assert hasattr(verification, 'last_email_sent'), "Champ last_email_sent manquant"
        print("✅ Champ last_email_sent présent")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def test_edge_cases():
    """Tester les cas limites"""
    print("\n🧪 TEST 4: Cas limites")
    
    user, verification = create_test_user()
    if not user:
        return False
    
    try:
        # Test 1: Aucun envoi précédent
        verification.last_email_sent = None
        verification.save()
        
        assert verification.can_resend_email, "Doit pouvoir envoyer sans envoi précédent"
        assert verification.time_until_next_resend is None, "Aucun temps d'attente sans envoi précédent"
        print("✅ Cas limite: Aucun envoi précédent")
        
        # Test 2: Envoi très récent (1 seconde)
        verification.last_email_sent = timezone.now() - timedelta(seconds=1)
        verification.save()
        
        assert not verification.can_resend_email, "Ne doit pas pouvoir envoyer après 1 seconde"
        print("✅ Cas limite: Envoi très récent")
        
        # Test 3: Envoi à la limite (5 minutes exactement)
        verification.last_email_sent = timezone.now() - timedelta(minutes=5)
        verification.save()
        
        # Note: peut être true ou false selon les microsecondes
        print(f"✅ Cas limite: Envoi à exactement 5 minutes - Peut envoyer: {verification.can_resend_email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        # Nettoyer
        user.delete()

def main():
    """Fonction principale"""
    print("🔐 TESTS DES AMÉLIORATIONS DE SÉCURITÉ EMAIL")
    print("=" * 50)
    
    tests = [
        ("Affichage de l'email", test_email_display),
        ("Système de cooldown", test_cooldown_system),
        ("Méthodes du modèle", test_model_methods),
        ("Cas limites", test_edge_cases),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n📊 RÉSUMÉ DES TESTS")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont réussis ! Les améliorations de sécurité fonctionnent correctement.")
        return True
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
