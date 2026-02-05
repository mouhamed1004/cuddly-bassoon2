#!/usr/bin/env python
"""
Test de l'envoi d'email Gmail SMTP - BLIZZ Gaming
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

from django.core.mail import send_mail
from django.conf import settings

def test_gmail_smtp():
    """Test de l'envoi d'email via Gmail SMTP"""
    print("📧 Test de l'envoi d'email Gmail SMTP...")
    print("=" * 50)
    
    try:
        # Vérifier la configuration
        print(f"✅ EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"✅ EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"✅ EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"✅ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"✅ EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD)}")
        print()
        
        # Demander l'email de test
        test_email = input("📧 Entrez votre email pour recevoir le test: ").strip()
        
        if not test_email:
            print("❌ Email non fourni")
            return False
        
        # Envoyer l'email de test
        print(f"📤 Envoi de l'email de test vers {test_email}...")
        
        subject = '🎮 Test Email BLIZZ Gaming - Vérification Gmail SMTP'
        message = f"""
Bonjour !

Ceci est un email de test pour vérifier que la configuration Gmail SMTP de BLIZZ Gaming fonctionne correctement.

Détails du test :
- Expéditeur : {settings.EMAIL_HOST_USER}
- Serveur SMTP : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
- TLS activé : {settings.EMAIL_USE_TLS}
- Date : {django.utils.timezone.now()}

Si vous recevez cet email, la configuration Gmail SMTP est fonctionnelle ! 🎉

Cordialement,
L'équipe BLIZZ Gaming
        """
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Test Email BLIZZ Gaming</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 20px; background: #f9f9f9; border-radius: 0 0 10px 10px; }}
                .success {{ color: #2ed573; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎮 BLIZZ Gaming</h1>
                    <p>Test Email Gmail SMTP</p>
                </div>
                <div class="content">
                    <h2>Bonjour !</h2>
                    <p>Ceci est un email de test pour vérifier que la configuration Gmail SMTP de <strong>BLIZZ Gaming</strong> fonctionne correctement.</p>
                    
                    <h3>Détails du test :</h3>
                    <ul>
                        <li><strong>Expéditeur :</strong> {settings.EMAIL_HOST_USER}</li>
                        <li><strong>Serveur SMTP :</strong> {settings.EMAIL_HOST}:{settings.EMAIL_PORT}</li>
                        <li><strong>TLS activé :</strong> {settings.EMAIL_USE_TLS}</li>
                        <li><strong>Date :</strong> {django.utils.timezone.now()}</li>
                    </ul>
                    
                    <p class="success">✅ Si vous recevez cet email, la configuration Gmail SMTP est fonctionnelle !</p>
                    
                    <p>🎉 La Phase 2 de vérification email Gmail est maintenant opérationnelle !</p>
                </div>
                <div class="footer">
                    <p>© 2024 BLIZZ Gaming. Tous droits réservés.</p>
                    <p>Cet email a été envoyé automatiquement pour tester la configuration SMTP.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Envoyer l'email
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[test_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result:
            print("✅ Email envoyé avec succès !")
            print(f"📧 Vérifiez votre boîte de réception : {test_email}")
            print("🎉 La configuration Gmail SMTP fonctionne parfaitement !")
            return True
        else:
            print("❌ Échec de l'envoi de l'email")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email: {e}")
        print("\n🔧 Vérifications à effectuer :")
        print("1. Vérifiez que le mot de passe d'application Gmail est correct")
        print("2. Vérifiez que la validation 2FA est activée sur Gmail")
        print("3. Vérifiez que l'email assistanceblizz@gmail.com est configuré correctement")
        return False

def main():
    """Fonction principale"""
    print("🚀 TEST GMAIL SMTP - BLIZZ GAMING")
    print("=" * 50)
    print("Ce script teste l'envoi d'email via Gmail SMTP")
    print("avec le compte assistanceblizz@gmail.com")
    print("=" * 50)
    print()
    
    success = test_gmail_smtp()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST RÉUSSI !")
        print("✅ La configuration Gmail SMTP est fonctionnelle")
        print("✅ La Phase 2 de vérification email est opérationnelle")
    else:
        print("❌ TEST ÉCHOUÉ")
        print("🔧 Vérifiez la configuration Gmail SMTP")
    print("=" * 50)

if __name__ == "__main__":
    main()
