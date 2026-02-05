#!/usr/bin/env python3
"""
Script de test du système d'email
Vérifie la configuration et teste l'envoi d'emails
"""
import os
import sys
import django
from datetime import datetime

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress


def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def check_email_configuration():
    """Vérifie la configuration email"""
    print_header("📧 CONFIGURATION EMAIL")
    
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Host User: {settings.EMAIL_HOST_USER}")
    print(f"Password configuré: {'✅ Oui' if settings.EMAIL_HOST_PASSWORD else '❌ Non'}")
    
    # Vérifier les paramètres allauth
    print(f"\n📝 Paramètres django-allauth:")
    account_email_verification = getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'optional')
    account_email_required = getattr(settings, 'ACCOUNT_EMAIL_REQUIRED', False)
    
    print(f"ACCOUNT_EMAIL_VERIFICATION: {account_email_verification}")
    print(f"ACCOUNT_EMAIL_REQUIRED: {account_email_required}")
    print(f"EMAIL_VERIFICATION_REQUIRED: {getattr(settings, 'EMAIL_VERIFICATION_REQUIRED', False)}")


def check_users_email_status():
    """Vérifie le statut des emails des utilisateurs"""
    print_header("👥 STATUT DES EMAILS UTILISATEURS")
    
    total_users = User.objects.count()
    users_with_verified_email = EmailAddress.objects.filter(verified=True).count()
    users_with_unverified_email = EmailAddress.objects.filter(verified=False).count()
    users_without_email_record = total_users - EmailAddress.objects.values('user').distinct().count()
    
    print(f"Total utilisateurs: {total_users}")
    print(f"Emails vérifiés: {users_with_verified_email} ({users_with_verified_email/total_users*100:.1f}%)" if total_users > 0 else "Emails vérifiés: 0")
    print(f"Emails non vérifiés: {users_with_unverified_email}")
    print(f"Sans enregistrement email: {users_without_email_record}")
    
    # Lister les utilisateurs non vérifiés
    print(f"\n📋 Utilisateurs avec email non vérifié:")
    unverified = EmailAddress.objects.filter(verified=False).select_related('user')
    
    if not unverified:
        print("✅ Tous les utilisateurs ont vérifié leur email (ou aucun utilisateur)")
    else:
        for i, email_obj in enumerate(unverified, 1):
            user = email_obj.user
            print(f"\n{i}. {user.username}")
            print(f"   Email: {email_obj.email}")
            print(f"   Inscrit: {user.date_joined.strftime('%d/%m/%Y %H:%M')}")
            print(f"   Dernier login: {user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Jamais'}")
            print(f"   Email primaire: {'✅ Oui' if email_obj.primary else '❌ Non'}")


def test_send_email():
    """Teste l'envoi d'un email"""
    print_header("📤 TEST D'ENVOI D'EMAIL")
    
    print("Tentative d'envoi d'un email de test...")
    
    try:
        send_mail(
            subject='Test Email - Blizz Gaming',
            message='Ceci est un email de test pour vérifier que le système fonctionne correctement.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Envoyer à soi-même
            fail_silently=False,
        )
        print("✅ Email envoyé avec succès !")
        print(f"   Destinataire: {settings.EMAIL_HOST_USER}")
        print(f"   Vérifiez votre boîte de réception (et spam)")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {str(e)}")
        print(f"\n🔍 Détails de l'erreur:")
        import traceback
        traceback.print_exc()


def check_email_templates():
    """Vérifie l'existence des templates d'email"""
    print_header("📄 TEMPLATES D'EMAIL")
    
    templates_to_check = [
        'account/email/email_confirmation_subject.txt',
        'account/email/email_confirmation_message.txt',
        'account/email/email_confirmation_message.html',
    ]
    
    from django.template.loader import get_template
    from django.template import TemplateDoesNotExist
    
    for template_path in templates_to_check:
        try:
            get_template(template_path)
            print(f"✅ {template_path}")
        except TemplateDoesNotExist:
            print(f"❌ {template_path} - MANQUANT")


def resend_verification_emails():
    """Propose de renvoyer les emails de vérification"""
    print_header("🔄 RENVOI DES EMAILS DE VÉRIFICATION")
    
    unverified = EmailAddress.objects.filter(verified=False).select_related('user')
    
    if not unverified:
        print("✅ Aucun email à renvoyer (tous vérifiés)")
        return
    
    print(f"Il y a {unverified.count()} utilisateur(s) avec email non vérifié.")
    print("\nVoulez-vous renvoyer les emails de vérification ? (y/n)")
    
    # En mode script, on ne demande pas confirmation
    # Pour utiliser cette fonction, décommentez et adaptez
    """
    response = input().lower()
    if response == 'y':
        from allauth.account.models import EmailConfirmation
        
        for email_obj in unverified:
            try:
                # Créer une nouvelle confirmation
                confirmation = EmailConfirmation.create(email_obj)
                confirmation.send()
                print(f"✅ Email envoyé à {email_obj.user.username} ({email_obj.email})")
            except Exception as e:
                print(f"❌ Erreur pour {email_obj.user.username}: {str(e)}")
    else:
        print("❌ Annulé")
    """
    print("ℹ️  Pour renvoyer les emails, décommentez la section dans le script")


def check_common_issues():
    """Vérifie les problèmes courants"""
    print_header("🔍 VÉRIFICATION DES PROBLÈMES COURANTS")
    
    issues = []
    
    # 1. Vérifier si le mot de passe email est configuré
    if not settings.EMAIL_HOST_PASSWORD:
        issues.append("❌ EMAIL_HOST_PASSWORD n'est pas configuré")
    else:
        print("✅ EMAIL_HOST_PASSWORD est configuré")
    
    # 2. Vérifier si l'email host user est configuré
    if not settings.EMAIL_HOST_USER:
        issues.append("❌ EMAIL_HOST_USER n'est pas configuré")
    else:
        print("✅ EMAIL_HOST_USER est configuré")
    
    # 3. Vérifier le backend email
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        issues.append("⚠️  EMAIL_BACKEND est en mode console (emails affichés dans la console)")
    else:
        print("✅ EMAIL_BACKEND est configuré pour SMTP")
    
    # 4. Vérifier la configuration allauth
    account_email_verification = getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'optional')
    if account_email_verification == 'none':
        issues.append("⚠️  ACCOUNT_EMAIL_VERIFICATION est 'none' (pas de vérification)")
    elif account_email_verification == 'optional':
        print("ℹ️  ACCOUNT_EMAIL_VERIFICATION est 'optional' (vérification optionnelle)")
    else:
        print("✅ ACCOUNT_EMAIL_VERIFICATION est 'mandatory' (vérification obligatoire)")
    
    # 5. Vérifier les limites Gmail
    print("\n📊 Limites Gmail:")
    print("   - Maximum 500 emails/jour")
    print("   - Maximum 100 destinataires par email")
    print("   - Risque de blocage si trop d'emails en peu de temps")
    
    if issues:
        print(f"\n⚠️  {len(issues)} problème(s) détecté(s):")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ Aucun problème majeur détecté")


def main():
    """Fonction principale"""
    print_header("🔍 TEST DU SYSTÈME D'EMAIL - BLIZZ GAMING")
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # 1. Vérifier la configuration
    check_email_configuration()
    
    # 2. Vérifier les problèmes courants
    check_common_issues()
    
    # 3. Vérifier le statut des utilisateurs
    check_users_email_status()
    
    # 4. Vérifier les templates
    check_email_templates()
    
    # 5. Tester l'envoi d'email
    print("\n" + "="*80)
    print("Voulez-vous tester l'envoi d'un email ? (Tapez 'y' pour oui, autre pour non)")
    print("Note: En mode script, le test est désactivé par défaut")
    print("="*80)
    # test_send_email()  # Décommentez pour tester
    
    # 6. Proposer de renvoyer les emails
    # resend_verification_emails()  # Décommentez pour utiliser
    
    print("\n" + "="*80)
    print("✅ Diagnostic terminé")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
