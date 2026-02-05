import requests
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from .models import ExchangeRate
import logging

logger = logging.getLogger(__name__)

class CurrencyService:
    """Service pour la gestion des conversions monétaires avec cache"""
    
    # API gratuite pour les taux de change
    EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/"
    CACHE_TIMEOUT = 3600  # 1 heure en secondes
    
    # Devises supportées par CinetPay
    CINETPAY_CURRENCIES = ['XOF', 'XAF', 'GNF']
    
    # Symboles des devises
    CURRENCY_SYMBOLS = {
        # Devises principales
        'EUR': '€',
        'USD': '$',
        'GBP': '£',
        
        # Afrique de l'Ouest et Centrale
        'XOF': 'FCFA',
        'XAF': 'FCFA',
        'GNF': 'GNF',
        'NGN': '₦',
        'GHS': '₵',
        
        # Maghreb
        'MAD': 'د.م.',
        'DZD': 'د.ج',
        'TND': 'د.ت',
        'EGP': 'ج.م',
        
        # Afrique de l'Est et Australe
        'KES': 'KSh',
        'TZS': 'TSh',
        'UGX': 'USh',
        'ZAR': 'R',
        'MUR': '₨',
        
        # Asie
        'JPY': '¥',
        'CNY': '¥',
        'INR': '₹',
        'KRW': '₩',
        'THB': '฿',
        'VND': '₫',
        'IDR': 'Rp',
        'PHP': '₱',
        'MYR': 'RM',
        'SGD': 'S$',
        
        # Amérique latine
        'BRL': 'R$',
        'MXN': '$',
        'ARS': '$',
        'CLP': '$',
        'COP': '$',
        'PEN': 'S/',
        'UYU': '$',
        'VES': 'Bs',
        
        # Amérique du Nord
        'CAD': 'CAD',
        'AUD': 'A$',
        'NZD': 'NZ$',
        
        # Europe
        'CHF': 'CHF',
        'SEK': 'kr',
        'NOK': 'kr',
        'DKK': 'kr',
        'PLN': 'zł',
        'CZK': 'Kč',
        'HUF': 'Ft',
        'RON': 'lei',
        'BGN': 'лв',
        'HRK': 'kn',
        'RSD': 'дин',
        'UAH': '₴',
        'RUB': '₽',
        'TRY': '₺',
    }
    
    @classmethod
    def get_exchange_rate(cls, from_currency, to_currency):
        """
        Récupère le taux de change entre deux devises
        Utilise un taux fixe pour EUR/XOF pour éviter les variations
        """
        if from_currency == to_currency:
            return Decimal('1.0')
        
        # Taux fixe pour EUR/XOF pour éviter les variations de prix
        if (from_currency == 'EUR' and to_currency == 'XOF') or (from_currency == 'XOF' and to_currency == 'EUR'):
            if from_currency == 'EUR':
                return Decimal('657.89')  # 1 EUR = 657.89 FCFA
            else:
                return Decimal('0.00152')  # 1 FCFA = 0.00152 EUR (1/657.89)
        
        # Vérifier le cache Django pour les autres devises
        cache_key = f"exchange_rate_{from_currency}_{to_currency}"
        cached_rate = cache.get(cache_key)
        if cached_rate:
            return Decimal(str(cached_rate))
        
        # Vérifier la base de données
        try:
            db_rate = ExchangeRate.objects.get(
                base_currency=from_currency,
                target_currency=to_currency
            )
            if db_rate.is_fresh:
                cache.set(cache_key, float(db_rate.rate), cls.CACHE_TIMEOUT)
                return db_rate.rate
        except ExchangeRate.DoesNotExist:
            pass
        
        # Récupérer depuis l'API externe
        try:
            rate = cls._fetch_rate_from_api(from_currency, to_currency)
            if rate:
                # Sauvegarder en base de données
                ExchangeRate.objects.update_or_create(
                    base_currency=from_currency,
                    target_currency=to_currency,
                    defaults={'rate': rate}
                )
                # Mettre en cache
                cache.set(cache_key, float(rate), cls.CACHE_TIMEOUT)
                return rate
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du taux {from_currency}->{to_currency}: {e}")
        
        # Fallback: retourner 1.0 si impossible de récupérer le taux
        logger.warning(f"Impossible de récupérer le taux {from_currency}->{to_currency}, utilisation de 1.0")
        return Decimal('1.0')
    
    @classmethod
    def _fetch_rate_from_api(cls, from_currency, to_currency):
        """Récupère le taux depuis l'API externe"""
        try:
            response = requests.get(
                f"{cls.EXCHANGE_API_URL}{from_currency}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if to_currency in data.get('rates', {}):
                return Decimal(str(data['rates'][to_currency]))
            
        except requests.RequestException as e:
            logger.error(f"Erreur API exchange rate: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Erreur parsing API response: {e}")
        
        return None
    
    @classmethod
    def convert_amount(cls, amount, from_currency, to_currency):
        """
        Convertit un montant d'une devise à une autre
        """
        if not amount:
            return Decimal('0.00')
        
        amount = Decimal(str(amount))
        rate = cls.get_exchange_rate(from_currency, to_currency)
        converted = amount * rate
        
        # Arrondir selon la devise de destination
        if to_currency in ['GNF']:
            # Devises sans centimes
            return converted.quantize(Decimal('1'))
        elif to_currency in ['XOF', 'XAF']:
            # Devises africaines : arrondir à l'unité pour éviter les erreurs de conversion
            return converted.quantize(Decimal('1'))
        elif from_currency in ['XOF', 'XAF'] and to_currency == 'EUR':
            # Conversion depuis XOF vers EUR : arrondir à 4 décimales pour plus de précision
            return converted.quantize(Decimal('0.0001'))
        else:
            # Autres devises : 2 décimales
            return converted.quantize(Decimal('0.01'))
    
    @classmethod
    def format_amount(cls, amount, currency):
        """
        Formate un montant avec le symbole de la devise
        """
        if not amount:
            amount = Decimal('0.00')
        
        amount = Decimal(str(amount))
        symbol = cls.CURRENCY_SYMBOLS.get(currency, currency)
        
        # Formatage selon la devise
        if currency in ['GNF']:
            # Pas de décimales pour le franc guinéen
            return f"{amount:,.0f} {symbol}"
        elif currency in ['XOF', 'XAF']:
            # Pas de décimales pour les francs CFA
            return f"{amount:,.0f} {symbol}"
        else:
            # 2 décimales pour EUR, USD, etc.
            return f"{symbol}{amount:,.2f}"
    
    @classmethod
    def get_user_currency(cls, user):
        """
        Récupère la devise préférée de l'utilisateur
        """
        if not user.is_authenticated:
            return 'EUR'  # Devise par défaut
        
        try:
            from .models import UserCurrency
            user_currency = UserCurrency.objects.get(user=user)
            return user_currency.preferred_currency
        except UserCurrency.DoesNotExist:
            return 'EUR'  # Devise par défaut
    
    @classmethod
    def convert_for_cinetpay(cls, amount, from_currency):
        """
        Convertit un montant vers une devise supportée par CinetPay
        Priorité: XOF > XAF > GNF
        """
        # Si déjà dans une devise CinetPay, pas de conversion
        if from_currency in cls.CINETPAY_CURRENCIES:
            return amount, from_currency
        
        # Convertir vers XOF par défaut (le plus utilisé en Afrique de l'Ouest)
        target_currency = 'XOF'
        converted_amount = cls.convert_amount(amount, from_currency, target_currency)
        
        return converted_amount, target_currency
    
    @classmethod
    def get_display_price(cls, base_amount, base_currency, user_currency):
        """
        Récupère le prix à afficher pour un utilisateur dans sa devise préférée
        Retourne un tuple (montant_converti, devise, montant_formaté)
        """
        converted_amount = cls.convert_amount(base_amount, base_currency, user_currency)
        formatted_amount = cls.format_amount(converted_amount, user_currency)
        
        return converted_amount, user_currency, formatted_amount
    
    @classmethod
    def refresh_all_rates(cls):
        """
        Rafraîchit tous les taux de change en base
        À utiliser dans une tâche cron
        """
        currencies = ['EUR', 'USD', 'XOF', 'XAF', 'GNF', 'GBP', 'CAD']
        updated_count = 0
        
        for base in currencies:
            for target in currencies:
                if base != target:
                    try:
                        rate = cls._fetch_rate_from_api(base, target)
                        if rate:
                            ExchangeRate.objects.update_or_create(
                                base_currency=base,
                                target_currency=target,
                                defaults={'rate': rate}
                            )
                            updated_count += 1
                    except Exception as e:
                        logger.error(f"Erreur refresh rate {base}->{target}: {e}")
        
        logger.info(f"Rafraîchi {updated_count} taux de change")
        return updated_count
    
    @classmethod
    def get_currencies_for_template(cls):
        """
        Retourne la liste des devises formatée pour les templates
        """
        from .models import UserCurrency
        currencies = []
        for code, name in UserCurrency.CURRENCY_CHOICES:
            symbol = cls.CURRENCY_SYMBOLS.get(code, code)
            currencies.append({
                'code': code,
                'name': name,
                'symbol': symbol
            })
        return currencies
