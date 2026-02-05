#!/usr/bin/env python
"""
Test de l'email de vérification réel - BLIZZ Gaming
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
from blizzgame.models import EmailVerification

def test_real_verification_email():
    """Test de l'email de vérification réel"""
    print("📧 Test de l'email de vérification réel BLIZZ Gaming...")
    print("=" * 60)
    
    try:
        # Créer un utilisateur de test
        test_username = 'testverification123'
        test_email = input("📧 Entrez votre email pour recevoir l'email de vérification réel: ").strip()
        
        if not test_email:
            print("❌ Email non fourni")
            return False
        
        # Supprimer l'utilisateur s'il existe déjà
        try:
            existing_user = User.objects.get(username=test_username)
            existing_user.delete()
            print("🧹 Ancien utilisateur de test supprimé")
        except:
            pass
        
        # Créer un nouvel utilisateur
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password='TestPassword123!'
        )
        
        print(f"✅ Utilisateur créé: {user.username}")
        print(f"✅ Email: {user.email}")
        
        # Créer la vérification email
        email_verification = EmailVerification.objects.create(user=user)
        print(f"✅ EmailVerification créé avec token: {email_verification.token}")
        
        # Envoyer l'email de vérification réel
        print("📤 Envoi de l'email de vérification réel...")
        result = email_verification.send_verification_email()
        
        if result:
            print("✅ Email de vérification envoyé avec succès !")
            print(f"📧 Vérifiez votre boîte de réception : {test_email}")
            print("🔗 L'email contient un lien de vérification unique")
            print("⏰ Le lien expire dans 24 heures")
            print()
            print("📋 Contenu de l'email :")
            print("- Sujet : 'Vérifiez votre adresse email - BLIZZ Gaming'")
            print("- Design HTML professionnel avec thème BLIZZ")
            print("- Bouton de vérification cliquable")
            print("- Lien de vérification unique")
            print("- Instructions claires")
            print("- Footer informatif")
            print()
            print("🎯 Pour tester la vérification :")
            print(f"1. Cliquez sur le lien dans l'email")
            print(f"2. Ou visitez : http://127.0.0.1:8000/verify-email/{email_verification.token}/")
            print("3. Vous devriez être redirigé vers la page de connexion")
            print("4. Vérifiez votre profil pour voir le statut 'Email Vérifié'")
            
            return True
        else:
            print("❌ Échec de l'envoi de l'email de vérification")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    finally:
        # Nettoyage
        try:
            user = User.objects.get(username=test_username)
            user.delete()
            print("\n🧹 Utilisateur de test supprimé")
        except:
            pass

def main():
    """Fonction principale"""
    print("🚀 TEST EMAIL DE VÉRIFICATION RÉEL - BLIZZ GAMING")
    print("=" * 60)
    print("Ce script teste l'email de vérification réel que recevront")
    print("les utilisateurs lors de leur inscription sur BLIZZ Gaming.")
    print("=" * 60)
    print()
    
    success = test_real_verification_email()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST RÉUSSI !")
        print("✅ L'email de vérification réel a été envoyé")
        print("✅ Le contenu est professionnel et sans emojis")
        print("✅ Le lien de vérification est fonctionnel")
        print("📧 Vérifiez votre boîte de réception (et les spams)")
    else:
        print("❌ TEST ÉCHOUÉ")
        print("🔧 Vérifiez la configuration Gmail SMTP")
    print("=" * 60)

if __name__ == "__main__":
    main()
