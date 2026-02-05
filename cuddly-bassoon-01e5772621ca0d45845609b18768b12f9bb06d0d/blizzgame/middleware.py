from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .models import UserBan
import logging

logger = logging.getLogger(__name__)

class BanCheckMiddleware:
    """
    Middleware pour vérifier si l'utilisateur connecté est banni
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si l'utilisateur est connecté
        if request.user.is_authenticated:
            try:
                # Vérifier s'il y a des bannissements actifs
                active_bans_qs = UserBan.objects.filter(
                    user=request.user,
                    is_active=True
                )
                # Filtrer côté Python pour compat champs ends_at/end_date
                now_ts = timezone.now()
                active_bans = []
                for b in active_bans_qs:
                    ban_end = getattr(b, 'ends_at', getattr(b, 'end_date', None))
                    if ban_end and ban_end < now_ts:
                        continue
                    active_bans.append(b)
                
                if active_bans:
                    # Récupérer le bannissement le plus récent
                    latest_ban = sorted(
                        active_bans,
                        key=lambda x: getattr(x, 'created_at', getattr(x, 'starts_at', now_ts)),
                        reverse=True
                    )[0]
                    
                    # Stocker les informations du bannissement dans la session
                    request.session['ban_info'] = {
                        'reason': latest_ban.reason,
                        'ban_type': latest_ban.ban_type,
                        'ends_at': (
                            getattr(latest_ban, 'ends_at', None) or getattr(latest_ban, 'end_date', None)
                        ).strftime('%d/%m/%Y à %H:%M') if (
                            getattr(latest_ban, 'ends_at', None) or getattr(latest_ban, 'end_date', None)
                        ) else '',
                        'details': latest_ban.details or '',
                    }
                    
                    # Déconnecter l'utilisateur
                    from django.contrib.auth import logout
                    logout(request)
                    
                    # Logger l'accès tenté
                    logger.warning(f"Utilisateur banni {request.user.username} a tenté d'accéder à {request.path}")
                    
                    # Rediriger vers la page d'information sur le bannissement
                    return redirect('banned_user')
                    
            except Exception as e:
                # En cas d'erreur, logger mais ne pas bloquer l'accès
                logger.error(f"Erreur dans BanCheckMiddleware: {e}")

        response = self.get_response(request)
        return response
