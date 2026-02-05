"""
Utilitaires pour l'intégration CinetPay
Gestion des paiements pour la boutique e-commerce (dropshipping) et transactions gaming
"""

import requests
import json
import uuid
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from .models import ShopCinetPayTransaction, Order, CinetPayTransaction, Transaction
import logging

logger = logging.getLogger(__name__)

class CinetPayAPI:
    def __init__(self):
        self.api_key = settings.CINETPAY_API_KEY
        self.site_id = settings.CINETPAY_SITE_ID
        self.secret_key = getattr(settings, 'CINETPAY_SECRET_KEY', '')
        self.test_mode = getattr(settings, 'CINETPAY_DROPSHIPPING_TEST_MODE', False)
        
        # URL de production CinetPay
        self.base_url = 'https://api-checkout.cinetpay.com/v2'

    def initiate_payment(self, order, customer_data):
        """
        Initie un paiement CinetPay pour une commande boutique
        """
        try:
            # Générer un ID de transaction unique
            transaction_id = f"SHOP_{order.order_number}_{uuid.uuid4().hex[:8]}"
            
            # URLs de callback
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            return_url = f"{base_url}{reverse('shop_payment_success', args=[order.id])}"
            notify_url = f"{base_url}{reverse('shop_cinetpay_notification')}"
            cancel_url = f"{base_url}{reverse('shop_payment_failed', args=[order.id])}"
            
            # Le montant de la commande est déjà converti dans la devise appropriée
            # par la vue shop_payment, donc pas besoin de reconvertir ici
            amount_xof = order.total_amount
            
            # Valider le montant
            is_valid, message = validate_cinetpay_amount(amount_xof, 'XOF')
            if not is_valid:
                logger.error(f"Montant dropshipping invalide: {message}")
                return {
                    'success': False,
                    'error': f"Montant invalide: {message}"
                }
            
            # Données pour CinetPay avec valeurs par défaut pour éviter MINIMUM_REQUIRED_FIELDS
            payment_data = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': transaction_id,
                'amount': int(amount_xof),  # CinetPay attend un entier
                'currency': 'XOF',  # Devise par défaut
                'alternative_currency': 'XOF',
                'description': f'Commande BLIZZ #{order.order_number}',
                'return_url': return_url,
                'notify_url': notify_url,
                'cancel_url': cancel_url,
                'customer_id': str(order.user.id) if order.user else 'guest',
                'customer_name': customer_data.get('customer_name') or order.customer_first_name or 'Client',
                'customer_surname': customer_data.get('customer_surname') or order.customer_last_name or 'BLIZZ',
                'customer_email': customer_data.get('customer_email') or order.customer_email or 'client@blizz.com',
                'customer_phone_number': customer_data.get('customer_phone_number') or order.customer_phone or '+221701234567',
                'customer_address': customer_data.get('customer_address') or order.shipping_address_line1 or 'Adresse non renseignée',
                'customer_city': customer_data.get('customer_city') or order.shipping_city or 'Dakar',
                'customer_country': customer_data.get('customer_country') or order.shipping_country or 'SN',
                'customer_state': customer_data.get('customer_state') or order.shipping_state or 'Dakar',
                'customer_zip_code': customer_data.get('customer_zip_code') or order.shipping_postal_code or '12345',
            }
            
            # Appel à l'API CinetPay
            response = requests.post(
                f"{self.base_url}/payment",
                json=payment_data,
                headers={'Content-Type': 'application/json'},
                timeout=20
            )

            # Tenter de parser la réponse même si status != 200 pour récupérer le message d'erreur
            try:
                result = response.json()
            except Exception:
                result = {'code': str(response.status_code), 'message': response.text}
            
            # Si status HTTP indique erreur réseau/service, retour explicite
            if response.status_code >= 500:
                logger.error(f"Erreur serveur CinetPay: {response.status_code} - {response.text}")
                return {'success': False, 'error': 'Erreur de connexion au service de paiement'}
            
            if result.get('code') == '201':
                # Succès - créer la transaction locale
                # Utiliser les données du formulaire avec fallback sécurisé
                customer_name = customer_data.get('customer_name') or order.customer_first_name or 'Client'
                customer_surname = customer_data.get('customer_surname') or order.customer_last_name or 'Blizz'
                customer_phone = customer_data.get('customer_phone_number') or order.customer_phone or '+221700000000'
                customer_email = customer_data.get('customer_email') or order.customer_email or 'client@blizz.com'
                customer_country = customer_data.get('customer_country') or order.shipping_country or 'SN'
                
                cinetpay_transaction = ShopCinetPayTransaction.objects.create(
                    order=order,
                    cinetpay_transaction_id=transaction_id,
                    payment_url=result['data']['payment_url'],
                    payment_token=result['data'].get('payment_token', ''),
                    customer_name=customer_name,
                    customer_surname=customer_surname,
                    customer_phone_number=customer_phone,
                    customer_email=customer_email,
                    customer_country=customer_country,
                    amount=order.total_amount,
                    currency='XOF',
                    status='pending'
                )
                
                logger.info(f"Paiement CinetPay initié: {transaction_id}")
                return {
                    'success': True,
                    'payment_url': result['data']['payment_url'],
                    'transaction_id': transaction_id,
                    'cinetpay_transaction': cinetpay_transaction
                }
            else:
                # Normaliser quelques erreurs fréquentes
                code = (result.get('code') or '').upper()
                error_msg = result.get('message', 'Erreur inconnue')
                if code == 'ERROR_AMOUNT_TOO_LOW':
                    error_msg = "Montant trop bas pour CinetPay. Augmentez le total (ex: > 100 XOF)."
                elif code == 'ERROR_AMOUNT_TOO_HIGH':
                    error_msg = "Montant trop élevé pour CinetPay. Réduisez le montant ou contactez le support."
                logger.error(f"Erreur CinetPay: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête CinetPay: {e}")
            return {
                'success': False,
                'error': 'Erreur de connexion au service de paiement'
            }
        except Exception as e:
            logger.error(f"Erreur inattendue CinetPay: {e}")
            return {
                'success': False,
                'error': 'Erreur interne du service de paiement'
            }

    def verify_payment(self, transaction_id):
        """
        Vérifie le statut d'un paiement CinetPay
        """
        try:
            verification_data = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': transaction_id
            }
            
            response = requests.post(
                f"{self.base_url}/payment/check",
                json=verification_data,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            return None

def handle_cinetpay_notification(notification_data):
    """
    Traite une notification CinetPay pour la boutique
    """
    try:
        transaction_id = notification_data.get('cpm_trans_id')
        if not transaction_id:
            logger.error("ID de transaction manquant dans la notification")
            return False
        
        # Trouver la transaction locale
        cinetpay_transaction = ShopCinetPayTransaction.objects.filter(
            cinetpay_transaction_id=transaction_id
        ).first()
        
        if not cinetpay_transaction:
            logger.error(f"Transaction CinetPay non trouvée: {transaction_id}")
            return False
        
        order = cinetpay_transaction.order
        
        # Vérifier le statut du paiement
        cinetpay_api = CinetPayAPI()
        verification_result = cinetpay_api.verify_payment(transaction_id)
        
        if not verification_result:
            logger.error(f"Impossible de vérifier le paiement: {transaction_id}")
            return False
        
        payment_status = verification_result.get('data', {}).get('payment_status')
        
        if payment_status == 'ACCEPTED':
            # Paiement réussi
            cinetpay_transaction.status = 'completed'
            cinetpay_transaction.completed_at = timezone.now()
            cinetpay_transaction.save()
            
            # Mettre à jour la commande
            order.payment_status = 'paid'
            order.status = 'processing'
            order.save()
            
            # TEMPORAIRE: Désactiver Shopify car Wiio ne livre pas au Sénégal
            # TODO: Réactiver quand un partenaire de livraison local sera trouvé
            logger.info(f"Paiement accepté pour: {order.order_number} - Shopify désactivé temporairement")
            
            # Créer la commande sur Shopify (DÉSACTIVÉ TEMPORAIREMENT)
            # from .shopify_utils import create_shopify_order_from_blizz_order, mark_order_as_paid_in_shopify
            # 
            # try:
            #     shopify_order = create_shopify_order_from_blizz_order(order)
            #     if shopify_order:
            #         # Marquer comme payée dans Shopify
            #         mark_order_as_paid_in_shopify(order)
            #         logger.info(f"Commande transférée vers Shopify: {order.order_number}")
            #     else:
            #         logger.error(f"Échec de création commande Shopify pour: {order.order_number}")
            # except Exception as e:
            #     logger.error(f"Erreur lors du transfert Shopify: {e}")
            
            return True
            
        elif payment_status == 'REFUSED':
            # Paiement échoué
            cinetpay_transaction.status = 'failed'
            cinetpay_transaction.save()
            
            order.payment_status = 'failed'
            order.status = 'cancelled'
            order.save()
            
            logger.info(f"Paiement échoué pour: {transaction_id}")
            return True
        
        else:
            logger.warning(f"Statut de paiement non géré: {payment_status}")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la notification: {e}")
        return False

def validate_cinetpay_amount(amount, currency='XOF'):
    """
    Valide que le montant est dans les limites acceptées par CinetPay
    VALIDATION DÉSACTIVÉE POUR LES TESTS - Tous les montants sont acceptés
    """
    # Limites CinetPay (DÉSACTIVÉES pour les tests)
    limits = {
        'XOF': {'min': 1, 'max': 2000000},    # 1 XOF à 2M XOF (validation minimale)
        'XAF': {'min': 1, 'max': 2000000},    # 1 XAF à 2M XAF
        'GNF': {'min': 1, 'max': 20000000},   # 1 GNF à 20M GNF
        'USD': {'min': 0.01, 'max': 3000},    # 0.01 USD à 3K USD
        'EUR': {'min': 0.01, 'max': 3000},    # 0.01 EUR à 3K EUR
    }
    
    if currency not in limits:
        return True, "Devise non supportée"
    
    limit = limits[currency]
    # Validation uniquement pour les montants extrêmes
    if amount <= 0:
        return False, f"Montant invalide: {amount} {currency}"
    elif amount > limit['max']:
        return False, f"Montant trop élevé. Maximum autorisé: {limit['max']} {currency}"
    
    # ✅ Accepter tous les montants > 0
    return True, "Montant valide"

def suggest_amount_alternatives(amount, currency='XOF'):
    """
    Suggère des alternatives pour les montants trop élevés
    """
    suggestions = []
    
    if currency == 'XOF':
        # Pour XOF, suggérer des montants plus raisonnables
        if amount > 1000000:  # Plus de 1M XOF
            suggestions.append({
                'amount': 500000,
                'currency': 'XOF',
                'description': '500,000 XOF (environ 760 EUR)'
            })
            suggestions.append({
                'amount': 1000000,
                'currency': 'XOF', 
                'description': '1,000,000 XOF (environ 1,520 EUR)'
            })
        elif amount > 500000:  # Plus de 500K XOF
            suggestions.append({
                'amount': 250000,
                'currency': 'XOF',
                'description': '250,000 XOF (environ 380 EUR)'
            })
            suggestions.append({
                'amount': 500000,
                'currency': 'XOF',
                'description': '500,000 XOF (environ 760 EUR)'
            })
    
    return suggestions

def convert_currency_for_cinetpay(amount, from_currency='EUR', to_currency='XOF'):
    """
    Convertit les devises pour CinetPay en utilisant CurrencyService
    Utilise les taux de change en temps réel avec fallback sur taux fixes
    """
    try:
        # Utiliser CurrencyService pour les taux de change réels
        from .currency_service import CurrencyService
        converted_amount = CurrencyService.convert_amount(amount, from_currency, to_currency)
        return float(converted_amount)
    except Exception as e:
        logger.warning(f"Erreur CurrencyService, utilisation des taux fixes: {e}")
        
        # Fallback sur les taux fixes (ancien système)
        exchange_rates = {
            'EUR': {
                'XOF': 655.957,  # 1 EUR = 655.957 XOF
                'XAF': 655.957,  # 1 EUR = 655.957 XAF
                'GNF': 9000,     # 1 EUR = 9000 GNF (approximatif)
                'USD': 1.1,      # 1 EUR = 1.1 USD (approximatif)
            },
            'USD': {
                'XOF': 596.32,   # 1 USD = 596.32 XOF
                'XAF': 596.32,   # 1 USD = 596.32 XAF
                'GNF': 8200,     # 1 USD = 8200 GNF (approximatif)
                'EUR': 0.91,     # 1 USD = 0.91 EUR (approximatif)
            }
        }
        
        if from_currency == to_currency:
            return float(amount)
        
        if from_currency in exchange_rates and to_currency in exchange_rates[from_currency]:
            rate = exchange_rates[from_currency][to_currency]
            converted_amount = float(amount) * rate
            
            # Valider le montant converti
            is_valid, message = validate_cinetpay_amount(converted_amount, to_currency)
            if not is_valid:
                logger.warning(f"Montant converti hors limites: {message}")
                # Retourner le montant quand même, mais avec un avertissement
                return round(converted_amount, 2)
            
            return round(converted_amount, 2)
        
        # Dernier fallback: retourner le montant original
        logger.warning(f"Conversion non supportée: {from_currency} -> {to_currency}")
        return float(amount)

def get_supported_countries():
    """
    Retourne la liste des pays supportés par CinetPay
    """
    return [
        ('CI', 'Côte d\'Ivoire'),
        ('SN', 'Sénégal'),
        ('BF', 'Burkina Faso'),
        ('ML', 'Mali'),
        ('NE', 'Niger'),
        ('TG', 'Togo'),
        ('BJ', 'Bénin'),
        ('GN', 'Guinée'),
        ('CM', 'Cameroun'),
        ('CD', 'RD Congo'),
    ]

def get_currency_for_country(country_code):
    """
    Retourne la devise appropriée selon le pays
    """
    currency_map = {
        'CI': 'XOF',  # Côte d'Ivoire
        'SN': 'XOF',  # Sénégal
        'BF': 'XOF',  # Burkina Faso
        'ML': 'XOF',  # Mali
        'NE': 'XOF',  # Niger
        'TG': 'XOF',  # Togo
        'BJ': 'XOF',  # Bénin
        'GN': 'GNF',  # Guinée
        'CM': 'XAF',  # Cameroun
        'CD': 'CDF',  # RD Congo
    }
    
    return currency_map.get(country_code, 'XOF')


class GamingCinetPayAPI(CinetPayAPI):
    """
    API CinetPay spécialisée pour les transactions gaming
    Hérite de CinetPayAPI mais adapte les URLs et la logique pour les transactions gaming
    """
    
    def initiate_payment(self, transaction, customer_data):
        """
        Initie un paiement CinetPay pour une transaction gaming
        """
        try:
            # Générer un ID de transaction unique pour gaming
            transaction_id = f"GAMING_{transaction.id}_{uuid.uuid4().hex[:8]}"
            
            # URLs de callback spécifiques au gaming
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            return_url = f"{base_url}{reverse('cinetpay_payment_success', args=[transaction.id])}"
            notify_url = f"{base_url}{reverse('gaming_cinetpay_notification')}"
            cancel_url = f"{base_url}{reverse('cinetpay_payment_failed', args=[transaction.id])}"
            
            # Convertir le montant en devise CinetPay (XOF par défaut)
            amount_eur = float(transaction.amount)
            amount_xof = convert_currency_for_cinetpay(amount_eur, 'EUR', 'XOF')
            
            # Log des données reçues pour débogage
            print(f"[CINETPAY API DEBUG] Données reçues - Name: '{customer_data.get('customer_name')}', Surname: '{customer_data.get('customer_surname')}', Email: '{customer_data.get('customer_email')}', Phone: '{customer_data.get('customer_phone_number')}'")
            logger.error(f"[CINETPAY API DEBUG] Données reçues - Name: '{customer_data.get('customer_name')}', Surname: '{customer_data.get('customer_surname')}', Email: '{customer_data.get('customer_email')}', Phone: '{customer_data.get('customer_phone_number')}'")
            
            # Données pour CinetPay avec valeurs par défaut pour éviter MINIMUM_REQUIRED_FIELDS
            payment_data = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': transaction_id,
                'amount': int(amount_xof),  # CinetPay attend un entier
                'currency': 'XOF',
                'alternative_currency': 'XOF',
                'description': f'Achat gaming BLIZZ - {transaction.post.title}',
                'return_url': return_url,
                'notify_url': notify_url,
                'cancel_url': cancel_url,
                'customer_id': str(transaction.buyer.id),
                'customer_name': customer_data.get('customer_name') or transaction.buyer.first_name or 'Gamer',
                'customer_surname': customer_data.get('customer_surname') or transaction.buyer.last_name or 'BLIZZ',
                'customer_email': customer_data.get('customer_email') or transaction.buyer.email or 'gamer@blizz.com',
                'customer_phone_number': customer_data.get('customer_phone_number') or '+221701234567',
                'customer_address': customer_data.get('customer_address') or 'Adresse non renseignée',
                'customer_city': customer_data.get('customer_city') or 'Dakar',
                'customer_country': customer_data.get('customer_country') or 'SN',
                'customer_state': customer_data.get('customer_state') or 'Dakar',
                'customer_zip_code': customer_data.get('customer_zip_code') or '12345',
            }
            
            # Log des données finales envoyées à CinetPay
            print(f"[CINETPAY API DEBUG] Données finales - Name: '{payment_data['customer_name']}', Surname: '{payment_data['customer_surname']}', Email: '{payment_data['customer_email']}', Phone: '{payment_data['customer_phone_number']}'")
            logger.error(f"[CINETPAY API DEBUG] Données finales - Name: '{payment_data['customer_name']}', Surname: '{payment_data['customer_surname']}', Email: '{payment_data['customer_email']}', Phone: '{payment_data['customer_phone_number']}'")
            
            # Log de TOUTES les données envoyées à CinetPay
            print(f"[CINETPAY API DEBUG] TOUTES LES DONNÉES: {payment_data}")
            logger.error(f"[CINETPAY API DEBUG] TOUTES LES DONNÉES: {payment_data}")
            
            # Appel à l'API CinetPay
            print(f"[CINETPAY API DEBUG] Appel à l'API CinetPay: {self.base_url}/payment")
            logger.error(f"[CINETPAY API DEBUG] Appel à l'API CinetPay: {self.base_url}/payment")
            
            response = requests.post(
                f"{self.base_url}/payment",
                json=payment_data,
                headers={'Content-Type': 'application/json'},
                timeout=20
            )
            
            print(f"[CINETPAY API DEBUG] Réponse CinetPay: {response.status_code} - {response.text}")
            logger.error(f"[CINETPAY API DEBUG] Réponse CinetPay: {response.status_code} - {response.text}")

            # Parser la réponse
            try:
                result = response.json()
            except Exception:
                result = {'code': str(response.status_code), 'message': response.text}
            
            # Gestion des erreurs serveur
            if response.status_code >= 500:
                logger.error(f"Erreur serveur CinetPay Gaming: {response.status_code} - {response.text}")
                return {'success': False, 'error': 'Erreur de connexion au service de paiement'}
            
            if result.get('code') == '201':
                # Succès - mettre à jour la transaction CinetPay existante avec gestion de transaction
                from django.db import transaction as db_transaction, connection
                
                try:
                    # Forcer la reconnexion si la connexion est fermée
                    connection.ensure_connection()
                    
                    with db_transaction.atomic():
                        cinetpay_transaction = CinetPayTransaction.objects.filter(transaction=transaction).first()
                        if cinetpay_transaction:
                            cinetpay_transaction.cinetpay_transaction_id = transaction_id
                            cinetpay_transaction.payment_url = result['data']['payment_url']
                            cinetpay_transaction.payment_token = result['data'].get('payment_token', '')
                            cinetpay_transaction.status = 'pending_payment'
                            cinetpay_transaction.save()
                    
                    logger.info(f"Paiement CinetPay Gaming initié: {transaction_id}")
                    return {
                        'success': True,
                        'payment_url': result['data']['payment_url'],
                        'transaction_id': transaction_id,
                        'cinetpay_transaction': cinetpay_transaction
                    }
                except Exception as db_error:
                    logger.error(f"Erreur DB lors de la sauvegarde CinetPay: {db_error}")
                    # Même si la sauvegarde échoue, retourner l'URL de paiement
                    return {
                        'success': True,
                        'payment_url': result['data']['payment_url'],
                        'transaction_id': transaction_id,
                        'cinetpay_transaction': None
                    }
            else:
                # Gestion des erreurs
                code = (result.get('code') or '').upper()
                error_msg = result.get('message', 'Erreur inconnue')
                if code == 'ERROR_AMOUNT_TOO_LOW':
                    error_msg = "Montant trop bas pour CinetPay. Minimum requis."
                elif code == 'ERROR_AMOUNT_TOO_HIGH':
                    error_msg = "Montant trop élevé pour CinetPay. Réduisez le montant ou contactez le support."
                logger.error(f"Erreur CinetPay Gaming: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête CinetPay Gaming: {e}")
            return {
                'success': False,
                'error': 'Erreur de connexion au service de paiement'
            }
        except Exception as e:
            logger.error(f"Erreur inattendue CinetPay Gaming: {e}")
            return {
                'success': False,
                'error': 'Erreur interne du service de paiement'
            }


def handle_gaming_cinetpay_notification(notification_data):
    """
    Traite une notification CinetPay pour les transactions gaming
    """
    try:
        transaction_id = notification_data.get('cpm_trans_id')
        if not transaction_id:
            logger.error("ID de transaction manquant dans la notification gaming")
            return False
        
        # Trouver la transaction CinetPay gaming
        cinetpay_transaction = CinetPayTransaction.objects.filter(
            cinetpay_transaction_id=transaction_id
        ).first()
        
        if not cinetpay_transaction:
            logger.error(f"Transaction CinetPay Gaming non trouvée: {transaction_id}")
            return False
        
        transaction = cinetpay_transaction.transaction
        
        # Vérifier le statut du paiement
        cinetpay_api = GamingCinetPayAPI()
        verification_result = cinetpay_api.verify_payment(transaction_id)
        
        if not verification_result:
            logger.error(f"Impossible de vérifier le paiement gaming: {transaction_id}")
            return False
        
        payment_status = verification_result.get('data', {}).get('payment_status')
        
        if payment_status == 'ACCEPTED':
            # Paiement réussi
            cinetpay_transaction.status = 'payment_received'
            cinetpay_transaction.completed_at = timezone.now()
            cinetpay_transaction.save()
            
            # Mettre à jour la transaction gaming
            transaction.status = 'processing'
            transaction.save()
            
            # MAINTENANT on met l'annonce en mode transaction (paiement confirmé)
            post = transaction.post
            post.is_in_transaction = True
            post.is_on_sale = False
            post.save()
            
            # Créer une notification pour le vendeur
            from .models import Notification
            Notification.objects.create(
                user=transaction.seller,
                type='transaction_update',
                title=' Paiement reçu',
                content=f'Le paiement pour "{transaction.post.title}" a été reçu. La transaction est maintenant active.',
                transaction=transaction
            )
            
            logger.info(f"Paiement gaming réussi pour: {transaction_id}, annonce marquée en transaction")
            return True
            
        elif payment_status == 'REFUSED':
            # Paiement échoué
            cinetpay_transaction.status = 'failed'
            cinetpay_transaction.save()
            
            transaction.status = 'cancelled'
            transaction.save()
            
            # Remettre l'annonce en vente
            post = transaction.post
            post.is_in_transaction = False
            post.is_on_sale = True
            post.save()
            
            logger.info(f"Paiement gaming échoué pour: {transaction_id}, annonce remise en vente")
            return True
        
        else:
            logger.warning(f"Statut de paiement gaming non géré: {payment_status}")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la notification gaming: {e}")
        return False


class DisputeResolutionAPI(CinetPayAPI):
    """
    API CinetPay spécialisée pour la résolution des litiges
    Gère les remboursements et payouts suite aux décisions admin
    """
    
    def process_transaction_refund(self, transaction, refund_amount=None):
        """
        Traite un remboursement vers l'acheteur pour une transaction normale
        """
        try:
            # Vérifier que la transaction a une transaction CinetPay
            if not hasattr(transaction, 'cinetpay_transaction'):
                return {
                    'success': False,
                    'error': 'Aucune transaction CinetPay trouvée pour cette transaction'
                }
            
            cinetpay_transaction = transaction.cinetpay_transaction
            
            # Utiliser le montant spécifié ou le montant total de la transaction
            if refund_amount is None:
                refund_amount = float(transaction.amount)
            else:
                refund_amount = float(refund_amount)
            
            # Générer un ID unique pour le remboursement
            refund_id = f"REFUND_{transaction.id.hex[:8]}_{uuid.uuid4().hex[:6]}"
            
            # Convertir le montant en XOF
            refund_amount_xof = convert_currency_for_cinetpay(refund_amount, 'EUR', 'XOF')
            
            # Données pour le remboursement CinetPay
            refund_data = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': refund_id,
                'original_transaction_id': cinetpay_transaction.cinetpay_transaction_id,
                'amount': int(refund_amount_xof),
                'currency': 'XOF',
                'description': f'Remboursement transaction #{transaction.id.hex[:8]} - {transaction.post.title}',
                'customer_phone_number': cinetpay_transaction.customer_phone_number,
                'customer_country': cinetpay_transaction.customer_country,
                'reason': f'Remboursement transaction - Annulation ou problème',
            }
            
            # Appel à l'API CinetPay pour remboursement
            response = requests.post(
                f"{self.base_url}/refund",
                json=refund_data,
                headers={'Content-Type': 'application/json'},
                timeout=20
            )
            
            # Parser la réponse
            try:
                result = response.json()
            except Exception:
                result = {'code': str(response.status_code), 'message': response.text}
            
            if response.status_code >= 500:
                logger.error(f"Erreur serveur CinetPay Refund: {response.status_code} - {response.text}")
                return {'success': False, 'error': 'Erreur de connexion au service de remboursement'}
            
            if result.get('code') == '201' or result.get('code') == '200':
                # Succès du remboursement
                cinetpay_transaction.status = 'refunded'
                cinetpay_transaction.save()
                
                # Mettre à jour la transaction principale
                transaction.status = 'refunded'
                transaction.save()
                
                # Créer une notification pour l'acheteur
                from .models import Notification
                Notification.objects.create(
                    user=transaction.buyer,
                    type='transaction_update',
                    title='Remboursement effectué',
                    content=f'Votre transaction concernant "{transaction.post.title}" a été remboursée. Montant: {refund_amount}€',
                    transaction=transaction
                )
                
                # Notification pour le vendeur
                Notification.objects.create(
                    user=transaction.seller,
                    type='transaction_update',
                    title='Transaction remboursée',
                    content=f'La transaction concernant "{transaction.post.title}" a été remboursée à l\'acheteur.',
                    transaction=transaction
                )
                
                logger.info(f"Remboursement transaction réussi: {refund_id}")
                return {
                    'success': True,
                    'refund_id': refund_id,
                    'amount_refunded': refund_amount
                }
            else:
                error_msg = result.get('message', 'Erreur lors du remboursement')
                logger.error(f"Erreur remboursement CinetPay: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du remboursement de transaction: {e}")
            return {
                'success': False,
                'error': 'Erreur interne lors du remboursement'
            }

    def process_refund(self, dispute):
        """
        Traite un remboursement vers l'acheteur suite à une résolution de litige
        """
        try:
            transaction = dispute.transaction
            
            # Vérifier que la transaction a une transaction CinetPay
            if not hasattr(transaction, 'cinetpay_transaction'):
                return {
                    'success': False,
                    'error': 'Aucune transaction CinetPay trouvée pour ce litige'
                }
            
            cinetpay_transaction = transaction.cinetpay_transaction
            
            # Générer un ID unique pour le remboursement
            refund_id = f"REFUND_{dispute.id.hex[:8]}_{uuid.uuid4().hex[:6]}"
            
            # Calculer le montant à rembourser (peut être partiel)
            refund_amount = dispute.refund_amount or dispute.disputed_amount
            refund_amount_xof = convert_currency_for_cinetpay(float(refund_amount), 'EUR', 'XOF')
            
            # Mode production - pas de simulation
            
            # Données pour le remboursement CinetPay
            refund_data = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': refund_id,
                'original_transaction_id': cinetpay_transaction.cinetpay_transaction_id,
                'amount': int(refund_amount_xof),
                'currency': 'XOF',
                'description': f'Remboursement litige #{dispute.id.hex[:8]} - {transaction.post.title}',
                'customer_phone_number': cinetpay_transaction.customer_phone_number,
                'customer_country': cinetpay_transaction.customer_country,
                'reason': f'Litige résolu en faveur de l\'acheteur: {dispute.get_reason_display()}',
            }
            
            # MODE MANUEL : Ne pas appeler l'API CinetPay pour les remboursements
            # Créer directement une PayoutRequest en attente pour traitement manuel
            logger.info(f"[REMBOURSEMENT MANUEL] Création d'une PayoutRequest pour traitement manuel: {refund_id}")
            
            # Simuler un succès pour créer la PayoutRequest
            result = {'code': '201', 'message': 'PayoutRequest créée pour traitement manuel'}
            
            if result.get('code') == '201' or result.get('code') == '200':
                # Succès du remboursement
                cinetpay_transaction.status = 'refunded'
                cinetpay_transaction.save()
                
                # Mettre à jour la transaction principale
                transaction.status = 'refunded'
                transaction.save()
                
                # Mettre à jour le litige
                dispute.status = 'resolved_buyer'
                dispute.resolution = 'refund'
                dispute.resolved_at = timezone.now()
                dispute.save()
                
                # Créer une PayoutRequest pour traçabilité (remboursement)
                from .models import PayoutRequest, EscrowTransaction
                
                # Créer ou récupérer l'EscrowTransaction
                # Note: EscrowTransaction n'a pas de champ 'transaction', seulement 'cinetpay_transaction'
                if hasattr(transaction, 'cinetpay_transaction'):
                    escrow_transaction, created = EscrowTransaction.objects.get_or_create(
                        cinetpay_transaction=transaction.cinetpay_transaction,
                        defaults={
                            'amount': float(refund_amount),
                            'currency': 'EUR',
                            'status': 'refunded'
                        }
                    )
                else:
                    # Si pas de CinetPayTransaction, créer une PayoutRequest sans EscrowTransaction
                    escrow_transaction = None
                
                # Créer la PayoutRequest pour le remboursement en attente pour traitement manuel
                PayoutRequest.objects.create(
                    escrow_transaction=escrow_transaction,
                    amount=refund_amount,  # 100% du montant pour les remboursements
                    original_amount=refund_amount,  # Même montant pour les remboursements (100%)
                    currency='EUR',
                    payout_type='buyer_refund',
                    status='pending',  # En attente pour traitement manuel
                    cinetpay_payout_id=refund_id,
                    recipient_phone=cinetpay_transaction.customer_phone_number,
                    recipient_country=cinetpay_transaction.customer_country,
                    recipient_operator='N/A',  # Pas d'opérateur pour les remboursements
                    completed_at=None  # Pas encore complété
                )
                
                # Créer une notification pour l'acheteur
                from .models import Notification
                Notification.objects.create(
                    user=transaction.buyer,
                    type='transaction_update',
                    title='Litige résolu - Remboursement effectué',
                    content=f'Votre litige concernant "{transaction.post.title}" a été résolu en votre faveur. Le remboursement de {refund_amount}€ a été effectué.',
                    transaction=transaction
                )
                
                # Notification pour le vendeur
                Notification.objects.create(
                    user=transaction.seller,
                    type='transaction_update',
                    title='Litige résolu - Remboursement acheteur',
                    content=f'Le litige concernant "{transaction.post.title}" a été résolu en faveur de l\'acheteur. Un remboursement a été effectué.',
                    transaction=transaction
                )
                
                logger.info(f"PayoutRequest créée pour traitement manuel (remboursement): {refund_id}")
                return {
                    'success': True,
                    'refund_id': refund_id,
                    'amount_refunded': refund_amount,
                    'manual_mode': True,
                    'message': 'PayoutRequest créée en attente de traitement manuel'
                }
            else:
                error_msg = result.get('message', 'Erreur lors du remboursement')
                logger.error(f"Erreur remboursement CinetPay: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du remboursement de litige: {e}")
            return {
                'success': False,
                'error': 'Erreur interne lors du remboursement'
            }
    
    def _simulate_refund(self, dispute, refund_id, refund_amount):
        """
        Simule un remboursement en mode test
        """
        try:
            transaction = dispute.transaction
            cinetpay_transaction = transaction.cinetpay_transaction
            
            # Mettre à jour le statut de la transaction CinetPay
            cinetpay_transaction.status = 'escrow_refunded'
            cinetpay_transaction.save()
            
            # Mettre à jour la transaction principale
            transaction.status = 'refunded'
            transaction.save()
            
            # Mettre à jour le litige
            dispute.status = 'resolved_buyer'
            dispute.resolution = 'refund'
            dispute.resolved_at = timezone.now()
            dispute.save()
            
            # Créer une notification pour l'acheteur
            from .models import Notification
            Notification.objects.create(
                user=transaction.buyer,
                type='transaction_update',
                title='🧪 [TEST] Litige résolu - Remboursement effectué',
                content=f'[MODE TEST] Votre litige concernant "{transaction.post.title}" a été résolu en votre faveur. Le remboursement de {refund_amount}€ a été simulé.',
                transaction=transaction
            )
            
            # Notification pour le vendeur
            Notification.objects.create(
                user=transaction.seller,
                type='transaction_update',
                title='🧪 [TEST] Litige résolu - Remboursement acheteur',
                content=f'[MODE TEST] Le litige concernant "{transaction.post.title}" a été résolu en faveur de l\'acheteur. Un remboursement a été simulé.',
                transaction=transaction
            )
            
            logger.info(f"🧪 Remboursement simulé réussi: {refund_id}")
            return {
                'success': True,
                'refund_id': refund_id,
                'amount_refunded': refund_amount,
                'test_mode': True
            }
            
        except Exception as e:
            logger.error(f"Erreur simulation remboursement: {e}")
            return {
                'success': False,
                'error': 'Erreur lors de la simulation du remboursement'
            }
    
    def add_contact(self, phone_number, country, operator):
        """
        Ajoute un contact à la liste CinetPay pour les transferts
        """
        try:
            contact_data = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'phone_number': phone_number,
                'country': country,
                'operator': operator,
            }
            
            response = requests.post(
                f"{self.base_url}/contact",
                json=contact_data,
                headers={'Content-Type': 'application/json'},
                timeout=20
            )
            
            result = response.json()
            logger.info(f"Ajout contact CinetPay: {response.status_code} - {result}")
            return result.get('code') == '201' or result.get('code') == '200'
            
        except Exception as e:
            logger.error(f"Erreur ajout contact: {e}")
            return False

    def process_transaction_payout_manual(self, transaction):
        """
        Traite un payout manuel vers le vendeur (CinetPay nécessite confirmation manuelle)
        """
        try:
            seller = transaction.seller
            logger.info(f"Payout manuel requis pour la transaction {transaction.id}, vendeur: {seller.username}")
            
            # Vérifier que le vendeur a une configuration de paiement
            if not hasattr(seller, 'payment_info'):
                return {
                    'success': False,
                    'error': 'Le vendeur n\'a pas configuré ses informations de paiement'
                }
            
            payment_info = seller.payment_info
            
            # Calculer les montants (90% vendeur, 10% commission)
            total_amount = float(transaction.amount)
            seller_amount = total_amount * 0.90
            platform_commission = total_amount * 0.10
            
            # Convertir en XOF
            seller_amount_xof = convert_currency_for_cinetpay(seller_amount, 'EUR', 'XOF')
            
            # Générer un ID unique pour le payout
            payout_id = f"PAYOUT_{transaction.id.hex[:8]}_{uuid.uuid4().hex[:6]}"
            
            # Déterminer les informations de payout selon la méthode préférée
            if payment_info.preferred_payment_method == 'mobile_money':
                recipient_phone = payment_info.phone_number
                recipient_operator = payment_info.operator
                payout_description = f'Mobile Money - {payment_info.get_operator_display()}'
            elif payment_info.preferred_payment_method == 'bank_transfer':
                recipient_phone = payment_info.account_number  # Utiliser le numéro de compte comme identifiant
                recipient_operator = payment_info.bank_name    # Utiliser le nom de la banque
                payout_description = f'Virement Bancaire - {payment_info.bank_name}'
            elif payment_info.preferred_payment_method == 'card':
                recipient_phone = payment_info.card_number     # Utiliser le numéro de carte comme identifiant
                recipient_operator = 'Carte Bancaire'          # Type de paiement
                payout_description = f'Carte Bancaire - {payment_info.card_holder_name}'
            else:
                # Fallback vers Mobile Money
                recipient_phone = payment_info.phone_number or 'N/A'
                recipient_operator = payment_info.operator or 'N/A'
                payout_description = 'Payout Standard'
            
            # Informations pour le payout manuel
            payout_info = {
                'payout_id': payout_id,
                'amount_eur': seller_amount,
                'amount_xof': int(seller_amount_xof),
                'recipient_phone': recipient_phone,
                'recipient_country': payment_info.country,
                'recipient_operator': recipient_operator,
                'description': f'Payout transaction #{transaction.id.hex[:8]} - {transaction.post.title}',
                'payout_description': payout_description,
                'payment_method': payment_info.preferred_payment_method,
                'transaction_id': transaction.id,
                'seller_username': seller.username
            }
            
            logger.info(f"PAYOUT MANUEL REQUIS:")
            logger.info(f"  - Payout ID: {payout_id}")
            logger.info(f"  - Montant: {seller_amount} EUR ({int(seller_amount_xof)} XOF)")
            logger.info(f"  - Méthode de paiement: {payment_info.get_preferred_payment_method_display()}")
            logger.info(f"  - Bénéficiaire: {recipient_phone} ({payment_info.country})")
            logger.info(f"  - Opérateur/Banque: {recipient_operator}")
            logger.info(f"  - Description: {payout_description}")
            logger.info(f"  - Transaction: {payout_info['description']}")
            
            # Créer une PayoutRequest pour traçabilité
            from .models import PayoutRequest, EscrowTransaction
            
            # Créer ou récupérer l'EscrowTransaction
            escrow_transaction, created = EscrowTransaction.objects.get_or_create(
                cinetpay_transaction=transaction.cinetpay_transaction,
                defaults={
                    'amount': seller_amount,  # Montant pour le vendeur
                    'currency': 'EUR',
                    'status': 'in_escrow'
                }
            )
            
            # Créer la PayoutRequest
            payout_request = PayoutRequest.objects.create(
                escrow_transaction=escrow_transaction,
                amount=seller_amount,
                currency='EUR',
                recipient_phone=recipient_phone,
                recipient_country=payment_info.country,
                recipient_operator=recipient_operator,
                status='pending',
                cinetpay_payout_id=payout_id
            )
            
            return {
                'success': True,
                'payout_id': payout_id,
                'amount': seller_amount,
                'platform_commission': platform_commission,
                'manual_payout_required': True,
                'payout_info': payout_info
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du payout manuel: {e}")
            return {
                'success': False,
                'error': 'Erreur interne lors du payout manuel'
            }

    def process_transaction_payout(self, transaction):
        """
        Traite un payout vers le vendeur suite à une transaction complétée
        Utilise les configurations de paiement du vendeur (SellerPaymentInfo)
        """
        try:
            seller = transaction.seller
            logger.info(f"Tentative de payout pour la transaction {transaction.id}, vendeur: {seller.username}")
            
            # Vérifier que le vendeur a une configuration de paiement
            if not hasattr(seller, 'payment_info'):
                logger.error(f"Vendeur {seller.username} n'a pas de payment_info")
                return {
                    'success': False,
                    'error': 'Le vendeur n\'a pas configuré ses informations de paiement'
                }
            
            payment_info = seller.payment_info
            
            # Vérifier que la configuration est complète et vérifiée
            from blizzgame.views import check_payment_setup
            if not check_payment_setup(seller):
                return {
                    'success': False,
                    'error': 'Configuration de paiement du vendeur incomplète ou non vérifiée'
                }
            
            # Vérifier que les informations sont vérifiées
            if not payment_info.is_verified:
                return {
                    'success': False,
                    'error': 'Les informations de paiement du vendeur n\'ont pas été vérifiées'
                }
            
            # Générer un ID unique pour le payout
            payout_id = f"PAYOUT_{transaction.id.hex[:8]}_{uuid.uuid4().hex[:6]}"
            
            # Calculer les montants (90% vendeur, 10% commission)
            total_amount = float(transaction.amount)
            seller_amount = total_amount * 0.90
            platform_commission = total_amount * 0.10
            
            # Convertir en XOF
            seller_amount_xof = convert_currency_for_cinetpay(seller_amount, 'EUR', 'XOF')
            
            # Préparer les données de payout selon la méthode de paiement
            payout_data = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': payout_id,
                'amount': int(seller_amount_xof),
                'currency': 'XOF',
                'description': f'Payout transaction #{transaction.id.hex[:8]} - {transaction.post.title}',
                'reason': f'Transaction complétée - Paiement vendeur',
            }
            
            # Ajouter les données spécifiques selon la méthode de paiement
            if payment_info.preferred_payment_method == 'mobile_money':
                payout_data.update({
                    'recipient_phone_number': payment_info.phone_number,
                    'recipient_country': payment_info.country,
                    'recipient_operator': payment_info.operator,
                })
            elif payment_info.preferred_payment_method == 'bank_transfer':
                payout_data.update({
                    'recipient_bank_name': payment_info.bank_name,
                    'recipient_account_number': payment_info.account_number,
                    'recipient_account_holder': payment_info.account_holder_name,
                    'recipient_swift_code': payment_info.swift_code,
                    'recipient_iban': payment_info.iban,
                })
            elif payment_info.preferred_payment_method == 'card':
                payout_data.update({
                    'recipient_card_number': payment_info.card_number,
                    'recipient_card_holder': payment_info.card_holder_name,
                })
            
            # Appel à l'API CinetPay pour payout
            response = requests.post(
                f"{self.base_url}/payout",
                json=payout_data,
                headers={'Content-Type': 'application/json'},
                timeout=20
            )
            
            # Parser la réponse
            try:
                result = response.json()
            except Exception:
                result = {'code': str(response.status_code), 'message': response.text}
            
            if response.status_code >= 500:
                logger.error(f"Erreur serveur CinetPay Payout: {response.status_code} - {response.text}")
                return {'success': False, 'error': 'Erreur de connexion au service de payout'}
            
            if result.get('code') == '201':
                # Succès du payout
                logger.info(f"Payout transaction réussi: {payout_id}")
                
                # Créer une PayoutRequest pour traçabilité
                from .models import PayoutRequest, EscrowTransaction
                
                # Créer ou récupérer l'EscrowTransaction
                escrow_transaction, created = EscrowTransaction.objects.get_or_create(
                    cinetpay_transaction=transaction.cinetpay_transaction,
                    defaults={
                        'amount': total_amount,
                        'currency': 'EUR',
                        'status': 'released'
                    }
                )
                
                # Créer la PayoutRequest
                payout_request = PayoutRequest.objects.create(
                    escrow_transaction=escrow_transaction,
                    amount=seller_amount,
                    currency='EUR',
                    status='completed',
                    cinetpay_payout_id=payout_id,
                    payout_method=payment_info.preferred_payment_method,
                    recipient_info=f"{payment_info.phone_number if payment_info.preferred_payment_method == 'mobile_money' else payment_info.account_number}"
                )
                
                logger.info(f"Payout transaction réussi: {payout_id}")
                return {
                    'success': True,
                    'payout_id': payout_id,
                    'amount': seller_amount,
                    'platform_commission': platform_commission
                }
            else:
                # Gestion des erreurs
                error_msg = result.get('message', 'Erreur lors du payout')
                logger.error(f"Erreur payout CinetPay: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du payout de transaction: {e}")
            return {
                'success': False,
                'error': 'Erreur interne lors du payout'
            }

    def process_payout(self, dispute):
        """
        Traite un payout vers le vendeur suite à une résolution de litige
        Utilise les configurations de paiement du vendeur (SellerPaymentInfo)
        """
        try:
            transaction = dispute.transaction
            seller = transaction.seller
            
            # Vérifier que le vendeur a une configuration de paiement
            if not hasattr(seller, 'payment_info'):
                return {
                    'success': False,
                    'error': 'Le vendeur n\'a pas configuré ses informations de paiement'
                }
            
            payment_info = seller.payment_info
            
            # Vérifier que la configuration est complète et vérifiée
            from blizzgame.views import check_payment_setup
            if not check_payment_setup(seller):
                return {
                    'success': False,
                    'error': 'Configuration de paiement du vendeur incomplète ou non vérifiée'
                }
            
            # Vérifier que les informations sont vérifiées
            if not payment_info.is_verified:
                return {
                    'success': False,
                    'error': 'Les informations de paiement du vendeur n\'ont pas été vérifiées'
                }
            
            # Générer un ID unique pour le payout
            payout_id = f"PAYOUT_{dispute.id.hex[:8]}_{uuid.uuid4().hex[:6]}"
            
            # Calculer les montants (90% vendeur, 10% commission)
            total_amount = float(dispute.disputed_amount)
            seller_amount = total_amount * 0.90
            platform_commission = total_amount * 0.10
            
            # Mode production - pas de simulation
            
            # Convertir en XOF
            seller_amount_xof = convert_currency_for_cinetpay(seller_amount, 'EUR', 'XOF')
            
            # Préparer les données de payout selon la méthode de paiement
            payout_data = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': payout_id,
                'amount': int(seller_amount_xof),
                'currency': 'XOF',
                'description': f'Payout litige #{dispute.id.hex[:8]} - {transaction.post.title}',
                'reason': f'Litige résolu en faveur du vendeur: {dispute.get_reason_display()}',
            }
            
            # Ajouter les données spécifiques selon la méthode de paiement
            if payment_info.preferred_payment_method == 'mobile_money':
                payout_data.update({
                    'recipient_phone_number': payment_info.phone_number,
                    'recipient_country': payment_info.country,
                    'recipient_operator': payment_info.operator,
                })
            elif payment_info.preferred_payment_method == 'bank_transfer':
                payout_data.update({
                    'recipient_bank_name': payment_info.bank_name,
                    'recipient_account_number': payment_info.account_number,
                    'recipient_account_holder': payment_info.account_holder_name,
                    'recipient_swift_code': payment_info.swift_code,
                    'recipient_iban': payment_info.iban,
                })
            elif payment_info.preferred_payment_method == 'card':
                payout_data.update({
                    'recipient_card_number': payment_info.card_number,
                    'recipient_card_holder': payment_info.card_holder_name,
                })
            
            # MODE MANUEL : Ne pas appeler l'API CinetPay
            # Créer directement une PayoutRequest en attente pour traitement manuel
            logger.info(f"[PAYOUT MANUEL] Création d'une PayoutRequest pour traitement manuel: {payout_id}")
            
            # Simuler un succès pour créer la PayoutRequest
            result = {'code': '201', 'message': 'PayoutRequest créée pour traitement manuel'}
            
            if result.get('code') == '201' or result.get('code') == '200':
                # Mettre à jour la transaction CinetPay si elle existe
                if hasattr(transaction, 'cinetpay_transaction'):
                    transaction.cinetpay_transaction.status = 'escrow_released'
                    transaction.cinetpay_transaction.save()
                
                # Mettre à jour la transaction principale
                transaction.status = 'completed'
                transaction.save()
                
                # Mettre à jour le litige
                dispute.status = 'resolved_seller'
                dispute.resolution = 'payout'
                dispute.resolved_at = timezone.now()
                dispute.save()
                
                # Créer une PayoutRequest pour traçabilité
                from .models import PayoutRequest, EscrowTransaction
                
                # Créer ou récupérer l'EscrowTransaction
                escrow_transaction, created = EscrowTransaction.objects.get_or_create(
                    cinetpay_transaction=transaction.cinetpay_transaction,
                    defaults={
                        'amount': total_amount,
                        'currency': 'EUR',
                        'status': 'released'
                    }
                )
                
                # Créer la PayoutRequest en attente pour traitement manuel
                # Récupérer le montant original depuis la transaction pour éviter les erreurs d'arrondi
                transaction_original_amount = float(transaction.amount) if hasattr(transaction, 'amount') else total_amount
                
                PayoutRequest.objects.create(
                    escrow_transaction=escrow_transaction,
                    amount=seller_amount,
                    original_amount=transaction_original_amount,  # Montant original de la transaction
                    currency='EUR',
                    payout_type='seller_payout',
                    status='pending',  # En attente pour traitement manuel
                    cinetpay_payout_id=payout_id,
                    recipient_phone=payment_info.phone_number if payment_info.preferred_payment_method == 'mobile_money' else '',
                    recipient_country=payment_info.country if hasattr(payment_info, 'country') else 'CI',
                    recipient_operator=payment_info.operator if hasattr(payment_info, 'operator') else 'Orange',
                    completed_at=None  # Pas encore complété
                )
                
                # Créer une notification pour le vendeur
                from .models import Notification
                Notification.objects.create(
                    user=transaction.seller,
                    type='transaction_update',
                    title='Litige résolu - Paiement effectué',
                    content=f'Votre litige concernant "{transaction.post.title}" a été résolu en votre faveur. Le paiement de {seller_amount}€ a été effectué.',
                    transaction=transaction
                )
                
                # Notification pour l'acheteur
                Notification.objects.create(
                    user=transaction.buyer,
                    type='transaction_update',
                    title='Litige résolu - Paiement vendeur',
                    content=f'Le litige concernant "{transaction.post.title}" a été résolu en faveur du vendeur.',
                    transaction=transaction
                )
                
                logger.info(f"PayoutRequest créée pour traitement manuel: {payout_id}")
                return {
                    'success': True,
                    'payout_id': payout_id,
                    'amount_paid': seller_amount,
                    'commission': platform_commission,
                    'manual_mode': True,
                    'message': 'PayoutRequest créée en attente de traitement manuel'
                }
            else:
                error_msg = result.get('message', 'Erreur lors du payout')
                logger.error(f"Erreur payout CinetPay: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du payout de litige: {e}")
            return {
                'success': False,
                'error': 'Erreur interne lors du payout'
            }
    
    def _simulate_payout(self, dispute, payout_id, seller_amount, platform_commission):
        """
        Simule un payout en mode test
        """
        try:
            transaction = dispute.transaction
            cinetpay_transaction = transaction.cinetpay_transaction
            
            # Mettre à jour le statut de la transaction CinetPay
            cinetpay_transaction.status = 'escrow_released'
            cinetpay_transaction.save()
            
            # Mettre à jour la transaction principale
            transaction.status = 'completed'
            transaction.save()
            
            # Mettre à jour le litige
            dispute.status = 'resolved_seller'
            dispute.resolution = 'payout'
            dispute.resolved_at = timezone.now()
            dispute.save()
            
            # Créer une notification pour le vendeur
            from .models import Notification
            Notification.objects.create(
                user=transaction.seller,
                type='transaction_update',
                title='🧪 [TEST] Litige résolu - Paiement effectué',
                content=f'[MODE TEST] Votre litige concernant "{transaction.post.title}" a été résolu en votre faveur. Le paiement de {seller_amount}€ a été simulé.',
                transaction=transaction
            )
            
            # Notification pour l'acheteur
            Notification.objects.create(
                user=transaction.buyer,
                type='transaction_update',
                title='🧪 [TEST] Litige résolu - Paiement vendeur',
                content=f'[MODE TEST] Le litige concernant "{transaction.post.title}" a été résolu en faveur du vendeur.',
                transaction=transaction
            )
            
            logger.info(f"🧪 Payout simulé réussi: {payout_id}")
            return {
                'success': True,
                'payout_id': payout_id,
                'amount_paid': seller_amount,
                'commission': platform_commission,
                'test_mode': True
            }
            
        except Exception as e:
            logger.error(f"Erreur simulation payout: {e}")
            return {
                'success': False,
                'error': 'Erreur lors de la simulation du payout'
            }