from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

class BlizzPasswordValidator:
    """
    Validateur personnalisé pour BLIZZ avec règles de sécurité renforcées
    """
    
    def validate(self, password, user=None):
        errors = []
        
        # Vérifier la longueur minimale
        if len(password) < 8:
            errors.append(_('Le mot de passe doit contenir au moins 8 caractères.'))
        
        # Vérifier la présence d'au moins une majuscule
        if not re.search(r'[A-Z]', password):
            errors.append(_('Le mot de passe doit contenir au moins une majuscule.'))
        
        # Vérifier la présence d'au moins une minuscule
        if not re.search(r'[a-z]', password):
            errors.append(_('Le mot de passe doit contenir au moins une minuscule.'))
        
        # Vérifier la présence d'au moins un chiffre
        if not re.search(r'\d', password):
            errors.append(_('Le mot de passe doit contenir au moins un chiffre.'))
        
        # Vérifier la présence d'au moins un caractère spécial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(_('Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*(),.?":{}|<>).'))
        
        # Vérifier qu'il n'y a pas de séquences répétitives
        if re.search(r'(.)\1{2,}', password):
            errors.append(_('Le mot de passe ne doit pas contenir de séquences répétitives.'))
        
        # Vérifier qu'il n'y a pas de séquences de clavier
        keyboard_sequences = ['qwerty', 'azerty', '123456', 'abcdef']
        password_lower = password.lower()
        for seq in keyboard_sequences:
            if seq in password_lower:
                errors.append(_('Le mot de passe ne doit pas contenir de séquences de clavier communes.'))
                break
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _("""
        Votre mot de passe doit contenir :
        • Au moins 8 caractères
        • Au moins une majuscule
        • Au moins une minuscule
        • Au moins un chiffre
        • Au moins un caractère spécial (!@#$%^&*(),.?":{}|<>)
        • Pas de séquences répétitives
        • Pas de séquences de clavier communes
        """)
