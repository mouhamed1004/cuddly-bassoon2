"""
Utilitaires de chiffrement sécurisé pour les données sensibles
Utilise Fernet (AES 128) avec une clé dérivée du SECRET_KEY Django
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Service de chiffrement sécurisé pour les données sensibles
    Utilise Fernet (AES 128) avec une clé dérivée du SECRET_KEY Django
    """
    
    _instance = None
    _fernet = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EncryptionService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._fernet is None:
            self._fernet = self._get_fernet_instance()
    
    def _get_fernet_instance(self):
        """
        Crée une instance Fernet avec une clé dérivée du SECRET_KEY Django
        """
        try:
            # Utiliser le SECRET_KEY Django comme base pour la clé de chiffrement
            secret_key = settings.SECRET_KEY
            if not secret_key:
                raise ImproperlyConfigured("SECRET_KEY Django non configuré")
            
            # Dériver une clé Fernet valide (32 bytes) du SECRET_KEY
            key_material = secret_key.encode('utf-8')
            # Utiliser SHA256 pour obtenir 32 bytes
            key_hash = hashlib.sha256(key_material).digest()
            # Encoder en base64 pour Fernet
            fernet_key = base64.urlsafe_b64encode(key_hash)
            
            return Fernet(fernet_key)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du chiffrement: {e}")
            raise ImproperlyConfigured(f"Impossible d'initialiser le chiffrement: {e}")
    
    def encrypt(self, data):
        """
        Chiffre une donnée sensible
        
        Args:
            data (str): Donnée à chiffrer
            
        Returns:
            str: Donnée chiffrée encodée en base64, ou None si erreur
        """
        if not data or data.strip() == '':
            return data
        
        try:
            # Convertir en bytes si c'est une string
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Chiffrer
            encrypted_data = self._fernet.encrypt(data_bytes)
            
            # Encoder en base64 pour stockage
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement: {e}")
            # En cas d'erreur, retourner la donnée originale pour éviter de casser l'application
            return data
    
    def decrypt(self, encrypted_data):
        """
        Déchiffre une donnée sensible
        
        Args:
            encrypted_data (str): Donnée chiffrée encodée en base64
            
        Returns:
            str: Donnée déchiffrée, ou None si erreur
        """
        if not encrypted_data or encrypted_data.strip() == '':
            return encrypted_data
        
        try:
            # Décoder depuis base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Déchiffrer
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            
            # Retourner en string
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement: {e}")
            # En cas d'erreur, retourner la donnée chiffrée pour éviter de casser l'application
            return encrypted_data
    
    def is_encrypted(self, data):
        """
        Vérifie si une donnée est chiffrée (heuristique simple)
        
        Args:
            data (str): Donnée à vérifier
            
        Returns:
            bool: True si la donnée semble chiffrée
        """
        if not data or not isinstance(data, str):
            return False
        
        try:
            # Tenter de décoder en base64
            base64.urlsafe_b64decode(data)
            # Si ça marche, c'est probablement chiffré
            return True
        except:
            return False

# Instance globale du service de chiffrement
encryption_service = EncryptionService()

def encrypt_sensitive_data(data):
    """
    Fonction utilitaire pour chiffrer des données sensibles
    
    Args:
        data (str): Donnée à chiffrer
        
    Returns:
        str: Donnée chiffrée ou originale si erreur
    """
    return encryption_service.encrypt(data)

def decrypt_sensitive_data(encrypted_data):
    """
    Fonction utilitaire pour déchiffrer des données sensibles
    
    Args:
        encrypted_data (str): Donnée chiffrée
        
    Returns:
        str: Donnée déchiffrée ou chiffrée si erreur
    """
    return encryption_service.decrypt(encrypted_data)

def is_data_encrypted(data):
    """
    Fonction utilitaire pour vérifier si une donnée est chiffrée
    
    Args:
        data (str): Donnée à vérifier
        
    Returns:
        bool: True si la donnée semble chiffrée
    """
    return encryption_service.is_encrypted(data)
