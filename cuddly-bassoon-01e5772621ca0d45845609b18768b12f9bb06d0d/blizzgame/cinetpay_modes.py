"""
Gestion des modes test CinetPay pour gaming et dropshipping
"""

from django.conf import settings

def get_cinetpay_test_mode(context='gaming'):
    """
    Retourne le mode test approprié selon le contexte
    
    Args:
        context (str): 'gaming' ou 'dropshipping'
    
    Returns:
        bool: True si en mode test, False sinon
    """
    if context == 'gaming':
        return getattr(settings, 'CINETPAY_GAMING_TEST_MODE', False)
    elif context == 'dropshipping':
        return getattr(settings, 'CINETPAY_DROPSHIPPING_TEST_MODE', False)
    else:
        # Par défaut, utiliser le mode gaming
        return getattr(settings, 'CINETPAY_GAMING_TEST_MODE', False)

def is_gaming_test_mode():
    """Vérifie si le mode test gaming est activé"""
    return get_cinetpay_test_mode('gaming')

def is_dropshipping_test_mode():
    """Vérifie si le mode test dropshipping est activé"""
    return get_cinetpay_test_mode('dropshipping')

def get_test_mode_status():
    """
    Retourne le statut des modes test pour affichage
    
    Returns:
        dict: Statut des modes test
    """
    return {
        'gaming_test_mode': is_gaming_test_mode(),
        'dropshipping_test_mode': is_dropshipping_test_mode(),
        'gaming_status': '🧪 Mode test' if is_gaming_test_mode() else '🔒 Mode production',
        'dropshipping_status': '🧪 Mode test' if is_dropshipping_test_mode() else '🔒 Mode production',
    }
