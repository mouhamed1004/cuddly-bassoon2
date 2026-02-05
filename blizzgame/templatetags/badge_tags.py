from django import template
from blizzgame.badge_config import get_seller_badge

register = template.Library()

@register.simple_tag
def get_user_badge(user):
    """Template tag to get user badge"""
    if hasattr(user, 'userreputation'):
        return user.userreputation.get_seller_badge()
    else:
        return get_seller_badge(0.0, 0)  # Bronze I par défaut (score 0, 0 transactions)


