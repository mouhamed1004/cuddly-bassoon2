from django import template
from django.utils.safestring import mark_safe
from ..currency_service import CurrencyService
from decimal import Decimal

register = template.Library()

@register.filter
def convert_currency(amount, currencies):
    """
    Convertit un montant d'une devise à une autre
    Usage: {{ price|convert_currency:"EUR,XOF" }}
    """
    if not amount or not currencies:
        return amount
    
    try:
        from_currency, to_currency = currencies.split(',')
        return CurrencyService.convert_amount(amount, from_currency.strip(), to_currency.strip())
    except (ValueError, AttributeError):
        return amount

@register.filter
def format_currency(amount, currency='EUR'):
    """
    Formate un montant avec le symbole de la devise
    Usage: {{ price|format_currency:"EUR" }}
    """
    return CurrencyService.format_amount(amount, currency)

@register.simple_tag(takes_context=True)
def display_price(context, amount, base_currency, user=None):
    """
    Affiche le prix dans la devise préférée de l'utilisateur
    Usage: {% display_price post.price "EUR" %} ou {% display_price post.price "EUR" request.user %}
    """
    if user is None:
        user = context.get('request').user if context.get('request') else None
    
    if not user or not user.is_authenticated:
        return CurrencyService.format_amount(amount, base_currency)
    
    user_currency = CurrencyService.get_user_currency(user)
    converted_amount, currency, formatted = CurrencyService.get_display_price(
        amount, base_currency, user_currency
    )
    
    return mark_safe(formatted)

@register.simple_tag
def display_price_with_original(amount, base_currency, user):
    """
    Affiche le prix converti avec le prix original en petit
    Usage: {% display_price_with_original post.price "EUR" request.user %}
    """
    if not user.is_authenticated:
        return CurrencyService.format_amount(amount, base_currency)
    
    user_currency = CurrencyService.get_user_currency(user)
    
    if user_currency == base_currency:
        return CurrencyService.format_amount(amount, base_currency)
    
    converted_amount, currency, formatted = CurrencyService.get_display_price(
        amount, base_currency, user_currency
    )
    
    original_formatted = CurrencyService.format_amount(amount, base_currency)
    
    html = f'''
    <span class="price-converted">
        <span class="main-price">{formatted}</span>
        <small class="original-price text-muted">({original_formatted})</small>
    </span>
    '''
    
    return mark_safe(html)

@register.inclusion_tag('currency/currency_selector.html', takes_context=True)
def currency_selector(context):
    """
    Affiche le sélecteur de devise
    Usage: {% currency_selector %}
    """
    user = context['request'].user
    current_currency = 'EUR'
    
    if user.is_authenticated:
        current_currency = CurrencyService.get_user_currency(user)
    
    currencies = [
        # Devises principales
        {'code': 'EUR', 'name': 'Euro (€)', 'symbol': '€'},
        {'code': 'USD', 'name': 'Dollar Américain ($)', 'symbol': '$'},
        {'code': 'GBP', 'name': 'Livre Sterling (£)', 'symbol': '£'},
        
        # Afrique de l'Ouest et Centrale
        {'code': 'XOF', 'name': 'Franc CFA Ouest (FCFA)', 'symbol': 'FCFA'},
        {'code': 'XAF', 'name': 'Franc CFA Central (FCFA)', 'symbol': 'FCFA'},
        {'code': 'GNF', 'name': 'Franc Guinéen (GNF)', 'symbol': 'GNF'},
        {'code': 'NGN', 'name': 'Naira Nigérian (₦)', 'symbol': '₦'},
        {'code': 'GHS', 'name': 'Cedi Ghanéen (₵)', 'symbol': '₵'},
        
        # Maghreb
        {'code': 'MAD', 'name': 'Dirham Marocain (د.م.)', 'symbol': 'د.م.'},
        {'code': 'DZD', 'name': 'Dinar Algérien (د.ج)', 'symbol': 'د.ج'},
        {'code': 'TND', 'name': 'Dinar Tunisien (د.ت)', 'symbol': 'د.ت'},
        {'code': 'EGP', 'name': 'Livre Égyptienne (ج.م)', 'symbol': 'ج.م'},
        
        # Asie
        {'code': 'JPY', 'name': 'Yen Japonais (¥)', 'symbol': '¥'},
        {'code': 'CNY', 'name': 'Yuan Chinois (¥)', 'symbol': '¥'},
        {'code': 'INR', 'name': 'Roupie Indienne (₹)', 'symbol': '₹'},
        {'code': 'KRW', 'name': 'Won Sud-Coréen (₩)', 'symbol': '₩'},
        {'code': 'THB', 'name': 'Baht Thaïlandais (฿)', 'symbol': '฿'},
        {'code': 'VND', 'name': 'Dong Vietnamien (₫)', 'symbol': '₫'},
        {'code': 'IDR', 'name': 'Roupie Indonésienne (Rp)', 'symbol': 'Rp'},
        {'code': 'PHP', 'name': 'Peso Philippin (₱)', 'symbol': '₱'},
        {'code': 'MYR', 'name': 'Ringgit Malaisien (RM)', 'symbol': 'RM'},
        {'code': 'SGD', 'name': 'Dollar Singapourien (S$)', 'symbol': 'S$'},
        
        # Amérique latine
        {'code': 'BRL', 'name': 'Real Brésilien (R$)', 'symbol': 'R$'},
        {'code': 'MXN', 'name': 'Peso Mexicain ($)', 'symbol': '$'},
        {'code': 'ARS', 'name': 'Peso Argentin ($)', 'symbol': '$'},
        {'code': 'CLP', 'name': 'Peso Chilien ($)', 'symbol': '$'},
        {'code': 'COP', 'name': 'Peso Colombien ($)', 'symbol': '$'},
        {'code': 'PEN', 'name': 'Sol Péruvien (S/)', 'symbol': 'S/'},
        {'code': 'UYU', 'name': 'Peso Uruguayen ($)', 'symbol': '$'},
        {'code': 'VES', 'name': 'Bolívar Vénézuélien (Bs)', 'symbol': 'Bs'},
        
        # Amérique du Nord
        {'code': 'CAD', 'name': 'Dollar Canadien (CAD)', 'symbol': 'CAD'},
        {'code': 'AUD', 'name': 'Dollar Australien (A$)', 'symbol': 'A$'},
        {'code': 'NZD', 'name': 'Dollar Néo-Zélandais (NZ$)', 'symbol': 'NZ$'},
        
        # Europe
        {'code': 'CHF', 'name': 'Franc Suisse (CHF)', 'symbol': 'CHF'},
        {'code': 'SEK', 'name': 'Couronne Suédoise (kr)', 'symbol': 'kr'},
        {'code': 'NOK', 'name': 'Couronne Norvégienne (kr)', 'symbol': 'kr'},
        {'code': 'DKK', 'name': 'Couronne Danoise (kr)', 'symbol': 'kr'},
        {'code': 'PLN', 'name': 'Zloty Polonais (zł)', 'symbol': 'zł'},
        {'code': 'CZK', 'name': 'Couronne Tchèque (Kč)', 'symbol': 'Kč'},
        {'code': 'HUF', 'name': 'Forint Hongrois (Ft)', 'symbol': 'Ft'},
        {'code': 'RON', 'name': 'Leu Roumain (lei)', 'symbol': 'lei'},
        {'code': 'BGN', 'name': 'Lev Bulgare (лв)', 'symbol': 'лв'},
        {'code': 'HRK', 'name': 'Kuna Croate (kn)', 'symbol': 'kn'},
        {'code': 'RSD', 'name': 'Dinar Serbe (дин)', 'symbol': 'дин'},
        {'code': 'UAH', 'name': 'Hryvnia Ukrainienne (₴)', 'symbol': '₴'},
        {'code': 'RUB', 'name': 'Rouble Russe (₽)', 'symbol': '₽'},
        {'code': 'TRY', 'name': 'Livre Turque (₺)', 'symbol': '₺'},
    ]
    
    return {
        'currencies': currencies,
        'current_currency': current_currency,
        'user': user,
    }

@register.simple_tag
def get_cinetpay_amount(amount, from_currency):
    """
    Convertit un montant vers une devise compatible CinetPay
    Usage: {% get_cinetpay_amount post.price "EUR" %}
    """
    converted_amount, target_currency = CurrencyService.convert_for_cinetpay(amount, from_currency)
    return {
        'amount': converted_amount,
        'currency': target_currency,
        'formatted': CurrencyService.format_amount(converted_amount, target_currency)
    }

@register.filter
def multiply_currency(amount, multiplier):
    """
    Multiplie un montant (utile pour les quantités)
    Usage: {{ price|multiply_currency:quantity }}
    """
    if not amount or not multiplier:
        return Decimal('0.00')
    
    return Decimal(str(amount)) * Decimal(str(multiplier))

@register.simple_tag
def currency_symbol(currency_code):
    """
    Retourne le symbole d'une devise
    Usage: {% currency_symbol "EUR" %}
    """
    return CurrencyService.CURRENCY_SYMBOLS.get(currency_code, currency_code)

@register.filter
def convert_notification_content(content, user):
    """
    Convertit les montants dans le contenu des notifications
    Usage: {{ notification.content|convert_notification_content:request.user }}
    """
    import re
    
    if not content or not user or not user.is_authenticated:
        return content
    
    try:
        user_currency = CurrencyService.get_user_currency(user)
        
        # Pattern pour trouver les montants avec € (ex: "15.50€", "100€")
        euro_pattern = r'(\d+(?:\.\d{1,2})?)\s*€'
        
        def replace_euro_amount(match):
            try:
                amount = float(match.group(1))
                converted_amount, currency, formatted = CurrencyService.get_display_price(
                    amount, 'EUR', user_currency
                )
                # Vérifier que le formatage est correct
                if formatted and not formatted.startswith('0.$'):
                    return formatted
                else:
                    # Fallback: retourner le montant original avec €
                    return f"{amount}€"
            except Exception as e:
                # En cas d'erreur, retourner le montant original
                return match.group(0)
        
        # Remplacer les montants en €
        converted_content = re.sub(euro_pattern, replace_euro_amount, content)
        
        return converted_content
        
    except Exception as e:
        # En cas d'erreur globale, retourner le contenu original
        return content
