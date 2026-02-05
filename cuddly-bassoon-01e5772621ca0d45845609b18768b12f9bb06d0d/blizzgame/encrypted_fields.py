"""
Champs Django personnalisés pour le chiffrement automatique des données sensibles
"""

from django.db import models
from django.core.exceptions import ValidationError
from .encryption_utils import encrypt_sensitive_data, decrypt_sensitive_data, is_data_encrypted
import logging

logger = logging.getLogger(__name__)

class EncryptedCharField(models.CharField):
    """
    Champ CharField qui chiffre automatiquement les données sensibles
    """
    
    def __init__(self, *args, **kwargs):
        # Marquer ce champ comme chiffré
        kwargs['help_text'] = kwargs.get('help_text', '') + ' (Chiffré automatiquement)'
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """
        Déchiffre la valeur lors de la lecture depuis la base de données
        """
        if value is None:
            return value
        
        try:
            # Vérifier si la donnée est chiffrée
            if is_data_encrypted(value):
                return decrypt_sensitive_data(value)
            else:
                # Si ce n'est pas chiffré, retourner tel quel (pour la migration)
                return value
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement de {self.name}: {e}")
            # En cas d'erreur, retourner la valeur originale
            return value
    
    def to_python(self, value):
        """
        Convertit la valeur Python en format approprié
        """
        if value is None:
            return value
        
        if isinstance(value, str):
            return value
        
        return str(value)
    
    def get_prep_value(self, value):
        """
        Prépare la valeur pour l'insertion en base de données (chiffrement)
        """
        if value is None or value == '':
            return value
        
        try:
            # Chiffrer la valeur avant de la sauvegarder
            return encrypt_sensitive_data(str(value))
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement de {self.name}: {e}")
            # En cas d'erreur, sauvegarder sans chiffrement pour éviter de casser l'application
            return str(value)

class EncryptedEmailField(models.EmailField):
    """
    Champ EmailField qui chiffre automatiquement les adresses email sensibles
    """
    
    def __init__(self, *args, **kwargs):
        # Marquer ce champ comme chiffré
        kwargs['help_text'] = kwargs.get('help_text', '') + ' (Chiffré automatiquement)'
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """
        Déchiffre la valeur lors de la lecture depuis la base de données
        """
        if value is None:
            return value
        
        try:
            # Vérifier si la donnée est chiffrée
            if is_data_encrypted(value):
                return decrypt_sensitive_data(value)
            else:
                # Si ce n'est pas chiffré, retourner tel quel (pour la migration)
                return value
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement de {self.name}: {e}")
            # En cas d'erreur, retourner la valeur originale
            return value
    
    def to_python(self, value):
        """
        Convertit la valeur Python en format approprié
        """
        if value is None:
            return value
        
        if isinstance(value, str):
            return value
        
        return str(value)
    
    def get_prep_value(self, value):
        """
        Prépare la valeur pour l'insertion en base de données (chiffrement)
        """
        if value is None or value == '':
            return value
        
        try:
            # Chiffrer la valeur avant de la sauvegarder
            return encrypt_sensitive_data(str(value))
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement de {self.name}: {e}")
            # En cas d'erreur, sauvegarder sans chiffrement pour éviter de casser l'application
            return str(value)
    
    def validate(self, value, model_instance):
        """
        Valide que la valeur est une adresse email valide
        """
        # Déchiffrer pour la validation si nécessaire
        if value and is_data_encrypted(value):
            try:
                decrypted_value = decrypt_sensitive_data(value)
                super().validate(decrypted_value, model_instance)
            except Exception as e:
                logger.error(f"Erreur lors de la validation de {self.name}: {e}")
                # Valider la valeur chiffrée si le déchiffrement échoue
                super().validate(value, model_instance)
        else:
            super().validate(value, model_instance)
