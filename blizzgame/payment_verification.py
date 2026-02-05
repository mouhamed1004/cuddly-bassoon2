"""
Système de vérification des informations de paiement vendeur
Protège contre les fausses informations et les pertes d'argent
"""

import re
import requests
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PaymentVerificationService:
    """
    Service de vérification des informations de paiement
    """
    
    @staticmethod
    def verify_phone_number(phone_number, country='SN'):
        """
        Vérifie la validité d'un numéro de téléphone
        """
        try:
            # Nettoyer le numéro
            phone = re.sub(r'[^\d+]', '', phone_number)
            
            # Vérifier le format selon le pays
            if country == 'SN':
                # Format sénégalais: +221XXXXXXXXX
                if not re.match(r'^\+221[0-9]{9}$', phone):
                    return False, "Format de numéro sénégalais invalide (+221XXXXXXXXX)"
            elif country == 'CI':
                # Format ivoirien: +225XXXXXXXXX
                if not re.match(r'^\+225[0-9]{9}$', phone):
                    return False, "Format de numéro ivoirien invalide (+225XXXXXXXXX)"
            elif country == 'BF':
                # Format burkinabé: +226XXXXXXXXX
                if not re.match(r'^\+226[0-9]{9}$', phone):
                    return False, "Format de numéro burkinabé invalide (+226XXXXXXXXX)"
            else:
                # Format international général
                if not re.match(r'^\+[1-9]\d{1,14}$', phone):
                    return False, "Format de numéro international invalide"
            
            return True, "Numéro valide"
            
        except Exception as e:
            logger.error(f"Erreur vérification téléphone: {e}")
            return False, "Erreur lors de la vérification"
    
    @staticmethod
    def verify_bank_account(account_number, bank_name, country='SN'):
        """
        Vérifie la validité d'un compte bancaire
        """
        try:
            # Vérifier que le numéro de compte n'est pas vide
            if not account_number or len(account_number.strip()) < 5:
                return False, "Numéro de compte trop court"
            
            # Vérifier que le nom de la banque n'est pas vide
            if not bank_name or len(bank_name.strip()) < 2:
                return False, "Nom de banque invalide"
            
            # Vérifier le format selon le pays
            if country == 'SN':
                # Format sénégalais: généralement 10-15 chiffres
                if not re.match(r'^[0-9]{10,15}$', account_number):
                    return False, "Format de compte bancaire sénégalais invalide"
            elif country == 'CI':
                # Format ivoirien: généralement 10-15 chiffres
                if not re.match(r'^[0-9]{10,15}$', account_number):
                    return False, "Format de compte bancaire ivoirien invalide"
            else:
                # Format international: alphanumérique
                if not re.match(r'^[A-Za-z0-9]{8,20}$', account_number):
                    return False, "Format de compte bancaire invalide"
            
            return True, "Compte bancaire valide"
            
        except Exception as e:
            logger.error(f"Erreur vérification compte bancaire: {e}")
            return False, "Erreur lors de la vérification"
    
    @staticmethod
    def verify_card_number(card_number):
        """
        Vérifie la validité d'un numéro de carte bancaire (algorithme de Luhn)
        """
        try:
            # Nettoyer le numéro
            card = re.sub(r'[^\d]', '', card_number)
            
            # Vérifier la longueur
            if len(card) < 13 or len(card) > 19:
                return False, "Longueur de carte invalide"
            
            # Algorithme de Luhn
            def luhn_checksum(card_num):
                def digits_of(n):
                    return [int(d) for d in str(n)]
                digits = digits_of(card_num)
                odd_digits = digits[-1::-2]
                even_digits = digits[-2::-2]
                checksum = sum(odd_digits)
                for d in even_digits:
                    checksum += sum(digits_of(d*2))
                return checksum % 10
            
            if luhn_checksum(card) == 0:
                return True, "Carte bancaire valide"
            else:
                return False, "Numéro de carte invalide"
                
        except Exception as e:
            logger.error(f"Erreur vérification carte: {e}")
            return False, "Erreur lors de la vérification"
    
    @staticmethod
    def verify_payment_info(payment_info):
        """
        Vérifie toutes les informations de paiement d'un vendeur
        """
        try:
            errors = []
            
            if payment_info.preferred_payment_method == 'mobile_money':
                # Vérifier le numéro de téléphone
                is_valid, message = PaymentVerificationService.verify_phone_number(
                    payment_info.phone_number, 
                    payment_info.country
                )
                if not is_valid:
                    errors.append(f"Téléphone: {message}")
                
                # Vérifier l'opérateur
                if not payment_info.operator:
                    errors.append("Opérateur Mobile Money requis")
                    
            elif payment_info.preferred_payment_method == 'bank_transfer':
                # Vérifier le compte bancaire
                is_valid, message = PaymentVerificationService.verify_bank_account(
                    payment_info.account_number,
                    payment_info.bank_name,
                    payment_info.country
                )
                if not is_valid:
                    errors.append(f"Compte bancaire: {message}")
                
                # Vérifier le nom du titulaire
                if not payment_info.account_holder_name or len(payment_info.account_holder_name.strip()) < 2:
                    errors.append("Nom du titulaire du compte requis")
                    
            elif payment_info.preferred_payment_method == 'card':
                # Vérifier le numéro de carte
                is_valid, message = PaymentVerificationService.verify_card_number(
                    payment_info.card_number
                )
                if not is_valid:
                    errors.append(f"Carte bancaire: {message}")
                
                # Vérifier le nom du titulaire
                if not payment_info.card_holder_name or len(payment_info.card_holder_name.strip()) < 2:
                    errors.append("Nom du titulaire de la carte requis")
            
            if errors:
                return False, errors
            else:
                return True, "Toutes les informations sont valides"
                
        except Exception as e:
            logger.error(f"Erreur vérification paiement: {e}")
            return False, [f"Erreur lors de la vérification: {str(e)}"]
    
    @staticmethod
    def simulate_payment_test(payment_info):
        """
        Simule un test de paiement pour vérifier les informations
        (En production, ceci ferait un appel à l'API CinetPay)
        """
        try:
            # En mode test, on simule une vérification
            if settings.CINETPAY_GAMING_TEST_MODE:
                # Simuler un délai de vérification
                import time
                time.sleep(1)
                
                # Simuler une vérification réussie (en production, ceci ferait un vrai appel API)
                return True, "Test de paiement simulé réussi"
            else:
                # En production, faire un vrai appel à l'API CinetPay
                # pour vérifier les informations
                return True, "Test de paiement en production (à implémenter)"
                
        except Exception as e:
            logger.error(f"Erreur test paiement: {e}")
            return False, f"Erreur lors du test: {str(e)}"

