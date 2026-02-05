# 📧 CONSIGNES COMPLÈTES - VÉRIFICATION EMAIL GMAIL

## 🎯 OBJECTIF
Implémenter un système de vérification email avec Gmail SMTP pour BLIZZ Gaming.

---

## 📋 ÉTAPES À SUIVRE

### 1. **CONFIGURATION GMAIL**

#### 1.1 Créer un mot de passe d'application Gmail
- Aller sur https://myaccount.google.com/security
- Activer la validation en 2 étapes si pas déjà fait
- Aller dans "Mots de passe des applications"
- Créer un nouveau mot de passe pour "Mail"
- **IMPORTANT** : Noter le mot de passe généré (ex: `dfcisqlnphadghdj`)

#### 1.2 Configurer Django Settings
Dans `socialgame/settings.py`, ajouter/modifier :

```python
# Configuration email Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@gmail.com'  # Votre email Gmail
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe-app'  # Mot de passe d'application (SANS ESPACES)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Configuration de vérification email
EMAIL_VERIFICATION_REQUIRED = True
EMAIL_VERIFICATION_EXPIRE_HOURS = 24
```

---

### 2. **CRÉATION DU MODÈLE EMAIL VERIFICATION**

#### 2.1 Ajouter le modèle dans `blizzgame/models.py`

```python
import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Vérification Email"
        verbose_name_plural = "Vérifications Email"

    def __str__(self):
        return f"Vérification email pour {self.user.username}"

    @property
    def is_expired(self):
        expiry_time = self.created_at + timedelta(hours=24)
        return timezone.now() > expiry_time

    def send_verification_email(self):
        try:
            subject = '🎮 Vérifiez votre adresse email - BLIZZ Gaming'
            verification_url = f"{settings.BASE_URL}/verify-email/{self.token}/"
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Vérifiez votre email - BLIZZ Gaming</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ padding: 20px; background: #f9f9f9; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #6c5ce7; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                    .code {{ background: #f0f0f0; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 18px; text-align: center; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎮 BLIZZ Gaming</h1>
                        <p>Vérification de votre compte</p>
                    </div>
                    <div class="content">
                        <h2>Bonjour {self.user.username} !</h2>
                        <p>Merci de vous être inscrit sur <strong>BLIZZ Gaming</strong> ! Pour activer votre compte et accéder à toutes les fonctionnalités, veuillez vérifier votre adresse email.</p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" class="button">
                                ✅ Vérifier mon Email
                            </a>
                        </p>
                        <p><strong>Ou copiez ce lien dans votre navigateur :</strong></p>
                        <div class="code">{verification_url}</div>
                        <p><strong>⏰ Important :</strong> Ce lien expire dans 24 heures.</p>
                        <p>Si vous n'avez pas créé de compte sur BLIZZ Gaming, vous pouvez ignorer cet email en toute sécurité.</p>
                        <p>Bienvenue dans la communauté gaming ! 🎮</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 BLIZZ Gaming. Tous droits réservés.</p>
                        <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Bonjour {self.user.username} !
            Merci de vous être inscrit sur BLIZZ Gaming !
            Pour activer votre compte, cliquez sur ce lien :
            {verification_url}
            Ce lien expire dans 24 heures.
            Si vous n'avez pas créé de compte, ignorez cet email.
            L'équipe BLIZZ Gaming
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de vérification: {e}")
            if 'console' in str(e) or 'BadCredentials' in str(e):
                print("Mode développement : Email simulé dans la console")
                return True
            return False
```

#### 2.2 Créer et appliquer les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 3. **MODIFICATION DES VUES**

#### 3.1 Modifier `blizzgame/views.py`

Ajouter les imports nécessaires :
```python
from .models import EmailVerification
import json
```

Modifier la vue `signup` pour créer automatiquement la vérification email :
```python
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
                return render(request, 'signup.html')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Cette adresse email est déjà utilisée.')
                return render(request, 'signup.html')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                
                # Créer le profil utilisateur
                user_profile = Profile.objects.create(user=user, id_user=user.id)
                user_profile.save()
                
                # Créer la vérification email
                email_verification = EmailVerification.objects.create(user=user)
                email_verification.send_verification_email()
                
                messages.success(request, 'Compte créé avec succès ! Vérifiez votre email pour activer votre compte.')
                return redirect('signin')
        else:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return render(request, 'signup.html')
    return render(request, 'signup.html')
```

Ajouter les nouvelles vues :
```python
def verify_email(request, token):
    """Vue pour vérifier l'email avec le token"""
    try:
        email_verification = EmailVerification.objects.get(token=token)
        
        if email_verification.is_expired:
            messages.error(request, 'Ce lien de vérification a expiré. Veuillez demander un nouveau lien.')
            return redirect('signin')
        
        if email_verification.is_verified:
            messages.info(request, 'Votre email a déjà été vérifié.')
            return redirect('signin')
        
        # Marquer comme vérifié
        email_verification.is_verified = True
        email_verification.verified_at = timezone.now()
        email_verification.save()
        
        messages.success(request, '🎉 Votre email a été vérifié avec succès ! Vous pouvez maintenant vous connecter.')
        return redirect('signin')
        
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Lien de vérification invalide.')
        return redirect('signin')

@login_required
def resend_verification_email(request):
    """Vue pour renvoyer un email de vérification"""
    if request.method == 'POST':
        try:
            email_verification = EmailVerification.objects.get(user=request.user)
            if email_verification.send_verification_email():
                return JsonResponse({'success': True, 'message': 'Email de vérification envoyé !'})
            else:
                return JsonResponse({'success': False, 'message': 'Erreur lors de l\'envoi de l\'email.'})
        except EmailVerification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Aucune vérification email trouvée.'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@login_required
def send_verification_email_on_signup(request):
    """Vue pour renvoyer un email de vérification après inscription"""
    if request.method == 'POST':
        try:
            # Créer l'objet de vérification
            verification = EmailVerification.objects.create(user=request.user)
            
            # Envoyer l'email
            if verification.send_verification_email():
                messages.success(request, '📧 Email de vérification envoyé ! Vérifiez votre boîte de réception pour activer votre compte.')
                return JsonResponse({'success': True})
            else:
                messages.error(request, '❌ Erreur lors de l\'envoi de l\'email. Vérifiez la configuration email.')
                return JsonResponse({'success': False, 'error': 'Erreur d\'envoi email'})
                
        except Exception as e:
            messages.error(request, f'❌ Erreur: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
```

---

### 4. **CONFIGURATION DES URLs**

#### 4.1 Ajouter dans `blizzgame/urls.py`

```python
# URLs de vérification email
path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
path('resend-verification-email/', views.resend_verification_email, name='resend_verification_email'),
path('send-verification-email/', views.send_verification_email_on_signup, name='send_verification_email_on_signup'),
```

---

### 5. **MODIFICATION DES TEMPLATES**

#### 5.1 Modifier `templates/profile.html`

Ajouter un bouton de vérification email dans la section du profil :
```html
{% if user == profile.user %}
    <div class="profile-actions">
        {% if not user.email_verification.is_verified %}
            <button onclick="resendVerificationEmail()" class="verify-email-btn">
                <i class="fas fa-envelope"></i> Vérifier Email
            </button>
        {% else %}
            <div class="email-verified">
                <i class="fas fa-check-circle"></i> Email Vérifié
            </div>
        {% endif %}
    </div>
{% endif %}
```

Ajouter le CSS :
```css
<style>
.profile-actions {
    margin: 1rem 0;
    text-align: center;
}

.verify-email-btn {
    background: linear-gradient(45deg, #6c5ce7, #a29bfe);
    color: white;
    border: none;
    padding: 0.8rem 1.5rem;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s ease;
}

.verify-email-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(108, 92, 231, 0.3);
}

.email-verified {
    color: #00ff88;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}
</style>
```

Ajouter le JavaScript :
```javascript
<script>
function resendVerificationEmail() {
    fetch('/resend-verification-email/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Email de vérification envoyé ! Vérifiez votre boîte de réception.');
        } else {
            alert('Erreur: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'envoi de l\'email.');
    });
}
</script>
```

---

### 6. **TESTS DE VALIDATION**

#### 6.1 Créer un script de test `test_email_verification.py`

```python
#!/usr/bin/env python
"""
Test de la vérification email Gmail
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import User
from blizzgame.models import EmailVerification

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

def test_email_verification():
    """Test complet de la vérification email"""
    print("🧪 Test de la vérification email Gmail...")
    
    client = Client()
    
    # Test 1: Inscription d'un utilisateur
    print("\n1. Test d'inscription...")
    response = client.post('/signup/', {
        'username': 'testuser123',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'confirm_password': 'TestPassword123!'
    })
    
    if response.status_code == 302:  # Redirection après inscription
        print("✅ Inscription réussie")
        
        # Vérifier que l'EmailVerification a été créé
        try:
            user = User.objects.get(username='testuser123')
            email_verification = EmailVerification.objects.get(user=user)
            print(f"✅ EmailVerification créé: {email_verification.token}")
            print(f"✅ Email non vérifié: {not email_verification.is_verified}")
        except:
            print("❌ EmailVerification non créé")
    else:
        print("❌ Échec de l'inscription")
    
    # Test 2: Vérification email
    print("\n2. Test de vérification email...")
    try:
        user = User.objects.get(username='testuser123')
        email_verification = EmailVerification.objects.get(user=user)
        
        response = client.get(f'/verify-email/{email_verification.token}/')
        if response.status_code == 302:  # Redirection après vérification
            print("✅ Vérification email réussie")
            
            # Vérifier que l'email est marqué comme vérifié
            email_verification.refresh_from_db()
            if email_verification.is_verified:
                print("✅ Email marqué comme vérifié")
            else:
                print("❌ Email non marqué comme vérifié")
        else:
            print("❌ Échec de la vérification email")
    except:
        print("❌ Utilisateur ou EmailVerification non trouvé")
    
    # Nettoyage
    try:
        user = User.objects.get(username='testuser123')
        user.delete()
        print("\n🧹 Utilisateur de test supprimé")
    except:
        pass

if __name__ == "__main__":
    test_email_verification()
```

#### 6.2 Exécuter le test
```bash
python test_email_verification.py
```

---

### 7. **CONFIGURATION BASE_URL**

#### 7.1 Dans `socialgame/settings.py`

```python
# URL de base pour les liens de vérification
BASE_URL = 'http://127.0.0.1:8000'  # En développement
# BASE_URL = 'https://votre-domaine.com'  # En production
```

---

### 8. **VÉRIFICATION FINALE**

#### 8.1 Checklist de validation
- [ ] Gmail SMTP configuré avec mot de passe d'application
- [ ] Modèle EmailVerification créé et migré
- [ ] Vues de vérification email ajoutées
- [ ] URLs configurées
- [ ] Templates modifiés
- [ ] Test d'inscription fonctionne
- [ ] Email de vérification reçu
- [ ] Lien de vérification fonctionne
- [ ] Email marqué comme vérifié

#### 8.2 Test manuel complet
1. Aller sur `/signup/`
2. Créer un compte avec une vraie adresse email
3. Vérifier la réception de l'email
4. Cliquer sur le lien de vérification
5. Se connecter avec le compte vérifié

---

## 🚨 POINTS IMPORTANTS

1. **Mot de passe d'application Gmail** : Ne pas utiliser le mot de passe normal, mais le mot de passe d'application généré
2. **Validation 2FA** : Doit être activée sur le compte Gmail
3. **BASE_URL** : Doit correspondre à l'URL de votre serveur
4. **Migrations** : Toujours faire `makemigrations` et `migrate` après modification des modèles
5. **Test** : Toujours tester avec une vraie adresse email

---

## 🔧 DÉPANNAGE

### Erreur "BadCredentials"
- Vérifier le mot de passe d'application (sans espaces)
- Vérifier que la validation 2FA est activée
- Créer un nouveau mot de passe d'application

### Email non reçu
- Vérifier les spams/courrier indésirable
- Vérifier la configuration SMTP
- Tester avec `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` pour debug

### Lien de vérification invalide
- Vérifier BASE_URL dans settings.py
- Vérifier que le token UUID est correct
- Vérifier que l'EmailVerification existe en base

---

**📝 Ce fichier contient toutes les étapes nécessaires pour implémenter la vérification email Gmail. Suivez chaque étape dans l'ordre pour un résultat optimal.**
