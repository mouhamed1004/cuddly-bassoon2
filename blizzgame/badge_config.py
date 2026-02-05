"""
Configuration des badges pour le système de réputation BLIZZ
Focus uniquement sur les vendeurs - Badges visuels personnalisés
"""

# Définir les badges vendeurs avec 12 niveaux progressifs
# Seuils exponentiels + Transactions minimales pour difficulté croissante
SELLER_BADGES = [
    # BRONZE (Niveaux 1-3) - Facile à atteindre
    {
        'name': 'Vendeur Bronze I',
        'level': 'bronze_1', 
        'min_score': 0,
        'min_transactions': 0,
        'color': '#CD7F32', 
        'icon': 'insignes/bronze/bronze_badge_1.png',
        'description': 'Vendeur débutant',
        'icon_symbol': '🥉',
        'tier': 1
    },
    {
        'name': 'Vendeur Bronze II',
        'level': 'bronze_2', 
        'min_score': 15,
        'min_transactions': 3,
        'color': '#CD7F32', 
        'icon': 'insignes/bronze/bronze_badge_2.png',
        'description': 'Vendeur bronze confirmé',
        'icon_symbol': '🥉⭐',
        'tier': 2
    },
    {
        'name': 'Vendeur Bronze III',
        'level': 'bronze_3', 
        'min_score': 30,
        'min_transactions': 5,
        'color': '#CD7F32', 
        'icon': 'insignes/bronze/bronze_badge_3.png',
        'description': 'Vendeur bronze expert',
        'icon_symbol': '🥉⭐⭐',
        'tier': 3
    },
    
    # ARGENT (Niveaux 4-6) - Difficulté moyenne
    {
        'name': 'Vendeur Argent I',
        'level': 'silver_1', 
        'min_score': 50,
        'min_transactions': 10,
        'color': '#C0C0C0', 
        'icon': 'insignes/argent/silver_badge_1.png',
        'description': 'Vendeur argent débutant',
        'icon_symbol': '🥈',
        'tier': 4
    },
    {
        'name': 'Vendeur Argent II',
        'level': 'silver_2', 
        'min_score': 65,
        'min_transactions': 15,
        'color': '#C0C0C0', 
        'icon': 'insignes/argent/silver_badge_2.png',
        'description': 'Vendeur argent confirmé',
        'icon_symbol': '🥈⭐',
        'tier': 5
    },
    {
        'name': 'Vendeur Argent III',
        'level': 'silver_3', 
        'min_score': 75,
        'min_transactions': 20,
        'color': '#C0C0C0', 
        'icon': 'insignes/argent/silver_badge_3.png',
        'description': 'Vendeur argent expert',
        'icon_symbol': '🥈⭐⭐',
        'tier': 6
    },
    
    # OR (Niveaux 7-9) - Difficile
    {
        'name': 'Vendeur Or I',
        'level': 'gold_1', 
        'min_score': 82,
        'min_transactions': 30,
        'color': '#FFD700', 
        'icon': 'insignes/or/gold_badge_1.png',
        'description': 'Vendeur or débutant',
        'icon_symbol': '🥇',
        'tier': 7
    },
    {
        'name': 'Vendeur Or II',
        'level': 'gold_2', 
        'min_score': 88,
        'min_transactions': 40,
        'color': '#FFD700', 
        'icon': 'insignes/or/gold_badge_2.png',
        'description': 'Vendeur or confirmé',
        'icon_symbol': '🥇⭐',
        'tier': 8
    },
    {
        'name': 'Vendeur Or III',
        'level': 'gold_3', 
        'min_score': 92,
        'min_transactions': 50,
        'color': '#FFD700', 
        'icon': 'insignes/or/gold_badge_3.png',
        'description': 'Vendeur or expert',
        'icon_symbol': '🥇⭐⭐',
        'tier': 9
    },
    
    # DIAMANT (Niveaux 10-12) - Très difficile (quasi-perfection requise)
    {
        'name': 'Vendeur Diamant I',
        'level': 'diamond_1', 
        'min_score': 95,
        'min_transactions': 75,
        'color': '#6C5CE7', 
        'icon': 'insignes/diamant/diamond_badge_1.png',
        'description': 'Vendeur diamant débutant',
        'icon_symbol': '💎',
        'tier': 10
    },
    {
        'name': 'Vendeur Diamant II',
        'level': 'diamond_2', 
        'min_score': 97,
        'min_transactions': 100,
        'color': '#6C5CE7', 
        'icon': 'insignes/diamant/diamond_badge_2.png',
        'description': 'Vendeur diamant confirmé',
        'icon_symbol': '💎⭐',
        'tier': 11
    },
    {
        'name': 'Vendeur Diamant III',
        'level': 'diamond_3', 
        'min_score': 99,
        'min_transactions': 150,
        'color': '#6C5CE7', 
        'icon': 'insignes/diamant/diamond_badge_3.png',
        'description': 'Maître Vendeur Légendaire',
        'icon_symbol': '💎⚡👑',
        'tier': 12
    },
]

# Traductions des noms de badges (extensible pour d'autres langues)
BADGE_TRANSLATIONS = {
    'fr': {
        'bronze_1': 'Vendeur Bronze I',
        'bronze_2': 'Vendeur Bronze II',
        'bronze_3': 'Vendeur Bronze III',
        'silver_1': 'Vendeur Argent I',
        'silver_2': 'Vendeur Argent II', 
        'silver_3': 'Vendeur Argent III',
        'gold_1': 'Vendeur Or I',
        'gold_2': 'Vendeur Or II',
        'gold_3': 'Vendeur Or III',
        'diamond_1': 'Vendeur Diamant I',
        'diamond_2': 'Vendeur Diamant II',
        'diamond_3': 'Vendeur Diamant III'
    },
    'en': {
        'bronze_1': 'Seller Bronze I',
        'bronze_2': 'Seller Bronze II',
        'bronze_3': 'Seller Bronze III',
        'silver_1': 'Seller Silver I',
        'silver_2': 'Seller Silver II',
        'silver_3': 'Seller Silver III',
        'gold_1': 'Seller Gold I',
        'gold_2': 'Seller Gold II',
        'gold_3': 'Seller Gold III',
        'diamond_1': 'Seller Diamond I',
        'diamond_2': 'Seller Diamond II',
        'diamond_3': 'Seller Diamond III'
    },
    'es': {
        'bronze_1': 'Vendedor Bronce I',
        'bronze_2': 'Vendedor Bronce II',
        'bronze_3': 'Vendedor Bronce III',
        'silver_1': 'Vendedor Plata I',
        'silver_2': 'Vendedor Plata II',
        'silver_3': 'Vendedor Plata III',
        'gold_1': 'Vendedor Oro I',
        'gold_2': 'Vendedor Oro II',
        'gold_3': 'Vendedor Oro III',
        'diamond_1': 'Vendedor Diamante I',
        'diamond_2': 'Vendedor Diamante II',
        'diamond_3': 'Vendedor Diamante III'
    }
}

def get_seller_badge(score, total_transactions=0):
    """
    Retourne le badge approprié selon le score vendeur ET le nombre de transactions
    
    Args:
        score: Score du vendeur (0-100)
        total_transactions: Nombre total de transactions effectuées
    
    Returns:
        dict: Badge correspondant aux critères
    """
    if score is None or score < 0:
        return SELLER_BADGES[0]  # Bronze I par défaut
    
    # Trouver le badge le plus élevé correspondant au score ET aux transactions
    appropriate_badge = SELLER_BADGES[0]
    for badge in SELLER_BADGES:
        # Le vendeur doit avoir BOTH le score ET le nombre de transactions requis
        if score >= badge['min_score'] and total_transactions >= badge['min_transactions']:
            appropriate_badge = badge
        else:
            # Dès qu'un critère n'est pas rempli, on arrête
            break
    
    return appropriate_badge

def get_badge_by_level(level):
    """Retourne un badge par son niveau"""
    for badge in SELLER_BADGES:
        if badge['level'] == level:
            return badge
    return SELLER_BADGES[0]  # Bronze par défaut

def get_translated_badge_name(badge, language='fr'):
    """Retourne le nom du badge traduit selon la langue spécifiée"""
    if language in BADGE_TRANSLATIONS and badge['level'] in BADGE_TRANSLATIONS[language]:
        return BADGE_TRANSLATIONS[language][badge['level']]
    return badge['name']  # Fallback vers le nom français par défaut

def get_seller_badge_with_translation(score, language='fr'):
    """Retourne le badge avec le nom traduit selon la langue"""
    badge = get_seller_badge(score)
    if badge:
        # Créer une copie du badge avec le nom traduit
        translated_badge = badge.copy()
        translated_badge['name'] = get_translated_badge_name(badge, language)
        return translated_badge
    return badge
