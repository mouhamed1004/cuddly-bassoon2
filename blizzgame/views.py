from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.conf import settings
from .models import *
# Shopify désactivé - Pas nécessaire pour le moment
# from .shopify_utils import create_shopify_order_from_blizz_order, sync_products_from_shopify
from .cinetpay_utils import CinetPayAPI, handle_cinetpay_notification, convert_currency_for_cinetpay, DisputeResolutionAPI
from .currency_service import CurrencyService
from .chat_views import *
import json
import uuid
from decimal import Decimal
import logging
import hmac
from django.db.models import Exists, OuterRef, Q
import re
import cloudinary
import cloudinary.uploader

def upload_image_to_cloudinary(image_file, folder_name):
    """
    Upload une image directement vers Cloudinary et retourne l'URL publique
    """
    try:
        # Configuration Cloudinary (déjà fait dans settings.py mais on s'assure)
        if not hasattr(cloudinary.config(), 'cloud_name') or not cloudinary.config().cloud_name:
            cloudinary_url = os.environ.get('CLOUDINARY_URL', '')
            if cloudinary_url:
                import re
                match = re.search(r'cloudinary://([^:]+):([^@]+)@(.+)', cloudinary_url)
                if match:
                    api_key, api_secret, cloud_name = match.groups()
                    cloudinary.config(
                        cloud_name=cloud_name,
                        api_key=api_key,
                        api_secret=api_secret,
                        secure=True
                    )
        
        # Upload vers Cloudinary
        result = cloudinary.uploader.upload(
            image_file,
            folder=folder_name,
            use_filename=True,
            unique_filename=True,
            resource_type="image"
        )
        
        # Retourner l'URL sécurisée
        return result.get('secure_url', result.get('url'))
        
    except Exception as e:
        # En cas d'erreur, log et retourner None pour utiliser le fallback
        logging.error(f"Erreur upload Cloudinary: {e}")
        return None

def create_or_update_message_notification(message, recipient):
    """
    Crée ou met à jour une notification groupée pour les messages
    """
    try:
        # Vérifier s'il existe déjà une notification non lue pour ce chat et cet expéditeur
        existing_notification = Notification.objects.filter(
            user=recipient,
            type='new_message',
            transaction=message.chat.transaction,
            is_read=False
        ).first()
        
        # Vérifier si c'est le même expéditeur (si le champ existe)
        if existing_notification and hasattr(existing_notification, 'sender_username'):
            if existing_notification.sender_username != message.sender.username:
                existing_notification = None
        
        if existing_notification:
            # Mettre à jour la notification existante
            if hasattr(existing_notification, 'message_count'):
                existing_notification.message_count += 1
            else:
                existing_notification.message_count = 2
            existing_notification.content = f"Vous avez reçu {existing_notification.message_count} messages de {message.sender.username}"
            existing_notification.created_at = timezone.now()  # Mettre à jour la date
            if hasattr(existing_notification, 'sender_username'):
                existing_notification.sender_username = message.sender.username
            existing_notification.save()
            return existing_notification
        else:
            # Créer une nouvelle notification
            notification_data = {
                'user': recipient,
                'type': 'new_message',
                'title': "Nouveau message",
                'content': f"Vous avez reçu un message de {message.sender.username}",
                'transaction': message.chat.transaction,
                'message': message,
                'message_count': 1
            }
            
            # Ajouter sender_username si le champ existe
            if hasattr(Notification, 'sender_username'):
                notification_data['sender_username'] = message.sender.username
            
            notification = Notification.objects.create(**notification_data)
            return notification
    except Exception as e:
        logging.error(f"Erreur lors de la création de la notification de message: {e}")
        return None

logger = logging.getLogger(__name__)

# ===== DÉCORATEURS PERSONNALISÉS =====

def email_verified_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur a vérifié son email
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('signin')
        
        try:
            from .models import EmailVerification
            email_verification = EmailVerification.objects.get(user=request.user)
            if not email_verification.is_verified:
                messages.error(request, 'Vous devez vérifier votre email avant d\'accéder à cette fonctionnalité. Vérifiez votre boîte de réception ou demandez un nouveau code de vérification.')
                return redirect('profile', username=request.user.username)
        except EmailVerification.DoesNotExist:
            messages.error(request, 'Vous devez vérifier votre email avant d\'accéder à cette fonctionnalité. Vérifiez votre boîte de réception ou demandez un nouveau code de vérification.')
            return redirect('profile', username=request.user.username)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ===== FONCTION DE REDIRECTION POUR LES FONCTIONNALITÉS DÉSACTIVÉES =====

def redirect_to_index(request, *args, **kwargs):
    """
    Redirige vers la page d'accueil pour toutes les fonctionnalités temporairement désactivées
    (Highlights, Chat, Amis, Abonnements)
    """
    from django.shortcuts import redirect
    # Message supprimé pour éviter les affichages inappropriés
    return redirect('index')

# ===== Vues existantes simples (stubs pour garantir l'import) =====

def index(request):
    from blizzgame.models import Post
    from django.db.models import Q, Case, When, IntegerField
    from django.core.paginator import Paginator
    from django.http import JsonResponse
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Récupérer tous les posts avec les relations nécessaires
        base_posts = Post.objects.select_related('author', 'author__profile', 'author__userreputation').prefetch_related('images', 'transactions')
        logger.info(f"Base posts query successful: {base_posts.count()} posts found")
    except Exception as e:
        logger.error(f"Error in base posts query: {e}")
        # Fallback sans relations si problème
        base_posts = Post.objects.all()
        logger.info(f"Fallback query successful: {base_posts.count()} posts found")
    
    try:
        # Appliquer les filtres
        filters = Q()
        
        # Filtre par jeu
        game_filter = request.GET.get('game')
        if game_filter and game_filter != 'all':
            filters &= Q(game_type=game_filter)
        
        # Filtre par prix minimum
        price_min = request.GET.get('price_min')
        if price_min:
            try:
                price_min_value = float(price_min)
                filters &= Q(price__gte=price_min_value)
            except ValueError:
                pass
        
        # Filtre par prix maximum
        price_max = request.GET.get('price_max')
        if price_max:
            try:
                price_max_value = float(price_max)
                filters &= Q(price__lte=price_max_value)
            except ValueError:
                pass
        
        # Filtre par pièces (recherche dans le titre ou la description)
        coins_filter = request.GET.get('coins')
        if coins_filter:
            filters &= Q(title__icontains=coins_filter) | Q(caption__icontains=coins_filter)
        
        # Filtre par niveau (recherche dans le titre ou la description)
        level_filter = request.GET.get('level')
        if level_filter:
            filters &= Q(title__icontains=level_filter) | Q(caption__icontains=level_filter)
        
        # Filtre par date
        date_filter = request.GET.get('date')
        if date_filter:
            from django.utils import timezone
            from datetime import timedelta
            now = timezone.now()
            
            if date_filter == 'today':
                filters &= Q(created_at__date=now.date())
            elif date_filter == 'week':
                week_ago = now - timedelta(days=7)
                filters &= Q(created_at__gte=week_ago)
            elif date_filter == 'month':
                month_ago = now - timedelta(days=30)
                filters &= Q(created_at__gte=month_ago)
        
        # Appliquer les filtres
        if filters:
            base_posts = base_posts.filter(filters)
            logger.info(f"Filters applied successfully")
        
    except Exception as e:
        logger.error(f"Error applying filters: {e}")
        # Continuer sans filtres si erreur
    
    try:
        # Organiser le feed selon l'ordre de priorité :
        # 1. Annonces récentes et disponibles (en haut)
        # 2. Annonces en transaction (au milieu) 
        # 3. Annonces vendues (tout en bas)
        
        posts_query = base_posts.annotate(
            priority=Case(
                # Priorité 1: Disponibles et récentes (en haut)
                When(
                    Q(is_on_sale=True) & Q(is_sold=False) & Q(is_in_transaction=False),
                    then=1
                ),
                # Priorité 2: En transaction (au milieu)
                When(
                    Q(is_in_transaction=True),
                    then=2
                ),
                # Priorité 3: Vendues (tout en bas)
                When(
                    Q(is_sold=True),
                    then=3
                ),
                # Priorité 4: Autres (désactivées, etc.)
                default=4,
                output_field=IntegerField()
            )
        )
        logger.info(f"Annotation successful: {posts_query.count()} posts")
    except Exception as e:
        logger.error(f"Error in annotation: {e}")
        # Fallback sans annotation si erreur
        posts_query = base_posts
        logger.info(f"Fallback query without annotation: {posts_query.count()} posts")
    
    try:
        # Appliquer le tri
        sort_by = request.GET.get('sort', 'created_at')
        if sort_by == 'price_asc':
            posts_query = posts_query.order_by('priority', 'price', '-created_at')
        elif sort_by == 'price_desc':
            posts_query = posts_query.order_by('priority', '-price', '-created_at')
        elif sort_by == 'title':
            posts_query = posts_query.order_by('priority', 'title', '-created_at')
        else:  # created_at par défaut
            posts_query = posts_query.order_by('priority', '-created_at')
        logger.info(f"Sorting applied: {sort_by}")
    except Exception as e:
        logger.error(f"Error in sorting: {e}")
        # Fallback tri simple si erreur
        posts_query = posts_query.order_by('-created_at')
        logger.info("Fallback sorting applied")
    
    try:
        # Pagination avec 12 posts par page
        paginator = Paginator(posts_query, 12)
        page_number = request.GET.get('page', 1)
        posts = paginator.get_page(page_number)
        logger.info(f"Pagination successful: {len(posts)} posts on page {page_number}")
    except Exception as e:
        logger.error(f"Error in pagination: {e}")
        # Fallback pagination simple si erreur
        posts = list(posts_query[:12])
        logger.info(f"Fallback pagination: {len(posts)} posts")
    
    # Si c'est une requête AJAX (pour le bouton "voir plus")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            posts_data = []
            for post in posts:
                try:
                    # Gestion sécurisée des propriétés
                    banner_url = '/static/images/default.png'
                    if hasattr(post, 'banner') and post.banner:
                        try:
                            banner_url = post.banner.url
                        except:
                            banner_url = '/static/images/default.png'
                    
                    posts_data.append({
                        'id': str(post.id),
                        'title': post.title or '',
                        'price': float(post.price) if post.price else 0.0,
                        'game_type': post.get_game_display_name() if hasattr(post, 'get_game_display_name') else str(post.game_type),
                        'user': str(post.user) if post.user else '',
                        'created_at': post.created_at.strftime('%d/%m/%Y') if post.created_at else '',
                        'is_sold': bool(post.is_sold),
                        'is_in_transaction': bool(post.is_in_transaction),
                        'is_on_sale': bool(post.is_on_sale),
                        'no_of_likes': int(post.no_of_likes) if post.no_of_likes else 0,
                        'banner_url': banner_url,
                        'time_since': post.time_since_created if hasattr(post, 'time_since_created') else '',
                    })
                except Exception as e:
                    logger.error(f"Error processing post {post.id}: {e}")
                    continue
            
            return JsonResponse({
                'posts': posts_data,
                'has_next': hasattr(posts, 'has_next') and posts.has_next() if hasattr(posts, 'has_next') else False,
                'next_page': posts.next_page_number() if hasattr(posts, 'has_next') and posts.has_next() else None,
                'current_page': posts.number if hasattr(posts, 'number') else 1,
                'total_pages': paginator.num_pages if 'paginator' in locals() else 1,
                'filters_applied': bool(filters) if 'filters' in locals() else False
            })
        except Exception as e:
            logger.error(f"Error in AJAX response: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    try:
        # Préparer les filtres actuels pour le template
        game_choices = Post.GAME_CHOICES
        current_filters = {
            'game': request.GET.get('game', ''),
            'price_min': request.GET.get('price_min', ''),
            'price_max': request.GET.get('price_max', ''),
            'coins': request.GET.get('coins', ''),
            'level': request.GET.get('level', ''),
            'date': request.GET.get('date', ''),
            'sort': request.GET.get('sort', 'created_at'),
        }
        
        # Gestion sécurisée des propriétés de pagination
        has_next = False
        next_page = None
        if hasattr(posts, 'has_next'):
            has_next = posts.has_next()
            if has_next and hasattr(posts, 'next_page_number'):
                next_page = posts.next_page_number()
        
        context = {
            'posts': posts,
            'game_choices': game_choices,
            'current_filters': current_filters,
            'has_next': has_next,
            'next_page': next_page,
            'page_title': 'Accueil - Blizz Gaming',
        }
        
        logger.info(f"Context prepared successfully for template rendering")
        return render(request, 'index.html', context)
        
    except Exception as e:
        logger.error(f"Error in template context preparation: {e}")
        # Fallback context minimal
        context = {
            'posts': [],
            'game_choices': [],
            'current_filters': {},
            'has_next': False,
            'next_page': None,
            'page_title': 'Accueil - Blizz Gaming',
        }
        return render(request, 'index.html', context)

def profile(request, username):
    user = get_object_or_404(User, username=username)
    prof = getattr(user, 'profile', None)
    
    # S'assurer qu'un profil existe toujours
    if prof is None:
        from .models import Profile
        prof = Profile.objects.create(user=user)
    # Filtrer les posts pour n'afficher que ceux qui sont disponibles à la vente
    # (pas vendus, pas supprimés, pas en transaction)
    user_posts = Post.objects.filter(
        author=user,
        is_sold=False,
        is_on_sale=True,
        is_in_transaction=False
    ).order_by('-created_at')
    
    # Calculer les statistiques pour la page profile
    total_sales = Post.objects.filter(author=user, is_sold=True).count()
    
    # Récupérer les données de réputation et badge
    reputation_summary = None
    if hasattr(user, 'userreputation'):
        reputation = user.userreputation
        seller_badge = reputation.get_seller_badge()
        current_score = float(reputation.seller_score) if reputation.seller_score else 0.0
        
        # Calculer le progrès vers le niveau suivant
        from .badge_config import SELLER_BADGES
        next_badge = None
        progress_percentage = 0
        current_transactions = reputation.seller_total_transactions
        
        # Trouver le badge suivant (celui dont au moins un critère n'est pas rempli)
        for badge in SELLER_BADGES:
            if current_score < badge['min_score'] or current_transactions < badge['min_transactions']:
                next_badge = badge
                break
        
        if next_badge and seller_badge:
            # Calculer la progression basée sur le score
            current_min_score = seller_badge['min_score']
            next_min_score = next_badge['min_score']
            score_progress = current_score - current_min_score
            score_range = next_min_score - current_min_score
            score_percentage = (score_progress / score_range) * 100 if score_range > 0 else 100
            
            # Calculer la progression basée sur les transactions
            current_min_trans = seller_badge['min_transactions']
            next_min_trans = next_badge['min_transactions']
            trans_progress = current_transactions - current_min_trans
            trans_range = next_min_trans - current_min_trans
            trans_percentage = (trans_progress / trans_range) * 100 if trans_range > 0 else 100
            
            # La progression globale est le minimum des deux (facteur limitant)
            progress_percentage = min(score_percentage, trans_percentage)
        elif not next_badge:
            # Niveau maximum atteint
            progress_percentage = 100
        
        reputation_summary = {
            'seller': {
                'badge': seller_badge,
                'score': current_score,
                'progress_percentage': min(progress_percentage, 100),
                'next_badge': next_badge
            }
        }
    
    context = {
        'profile': prof,
        'user_obj': user,
        'user_profile': prof,  # Pour compatibilité avec le template
        'posts': user_posts,
        'total_sales': total_sales,
        'rating': 0,  # Initialisé à zéro
        'reputation_summary': reputation_summary,
    }
    return render(request, 'profile.html', context)

@login_required
def settings(request):
    if request.method == 'POST':
        prof = getattr(request.user, 'profile', None)
        if prof is None:
            from .models import Profile
            prof = Profile.objects.create(user=request.user)
        prof.bio = request.POST.get('bio', prof.bio)
        
        # Gestion du changement de pseudo
        new_username = request.POST.get('username', '').strip()
        if new_username and new_username != request.user.username:
            # Vérifier si l'utilisateur peut changer son pseudo
            if not prof.can_change_username:
                messages.error(request, f'Vous ne pouvez changer votre pseudo que tous les deux mois. Prochain changement possible le : {prof.next_username_change_date.strftime("%d/%m/%Y à %H:%M")}')
                return redirect('settings')
            
            # Vérifier si le nouveau pseudo est disponible
            from django.contrib.auth.models import User
            if User.objects.filter(username=new_username).exists():
                messages.error(request, 'Ce nom d\'utilisateur est déjà pris.')
                return redirect('settings')
            
            # Changer le pseudo
            request.user.username = new_username
            request.user.save()
            
            # Mettre à jour la date du dernier changement
            from django.utils import timezone
            prof.last_username_change = timezone.now()
            prof.save()
            
            messages.success(request, 'Pseudo modifié avec succès !')
            return redirect('settings')
        
        # Gestion des images avec upload direct vers Cloudinary
        if 'profileimg' in request.FILES:
            cloudinary_url = upload_image_to_cloudinary(request.FILES['profileimg'], 'profile_images')
            if cloudinary_url:
                # Sauver l'URL Cloudinary seulement si le champ existe
                try:
                    prof.profileimg_url = cloudinary_url
                except AttributeError:
                    # Le champ n'existe pas encore, migration pas appliquée
                    pass
                # Garder aussi le champ traditionnel pour compatibilité
                prof.profileimg = request.FILES['profileimg']
            else:
                # Fallback si Cloudinary échoue
                prof.profileimg = request.FILES['profileimg']
                
        if 'banner' in request.FILES:
            cloudinary_url = upload_image_to_cloudinary(request.FILES['banner'], 'banner_images')
            if cloudinary_url:
                # Sauver l'URL Cloudinary seulement si le champ existe
                try:
                    prof.banner_url = cloudinary_url
                except AttributeError:
                    # Le champ n'existe pas encore, migration pas appliquée
                    pass
                # Garder aussi le champ traditionnel pour compatibilité
                prof.banner = request.FILES['banner']
            else:
                # Fallback si Cloudinary échoue
                prof.banner = request.FILES['banner']
        
        # Gestion des jeux favoris
        favorite_games = request.POST.getlist('favorite_games')
        prof.favorite_games = favorite_games
        
        # Gestion des informations de payout
        payout_phone = request.POST.get('payout_phone', '').strip()
        payout_country = request.POST.get('payout_country', '').strip()
        payout_operator = request.POST.get('payout_operator', '').strip()
        
        if payout_phone and payout_country and payout_operator:
            prof.payout_phone = payout_phone
            prof.payout_country = payout_country
            prof.payout_operator = payout_operator
            # Marquer comme vérifié si toutes les infos sont fournies
            prof.payout_verified = True
        else:
            # Si des infos sont manquantes, marquer comme non vérifié
            prof.payout_verified = False
        
        prof.save()
        messages.success(request, 'Profil mis à jour')
        return redirect('settings')
    
    # Préparer les données pour le template
    from blizzgame.models import Profile
    game_choices = Profile.GAME_CHOICES
    
    # S'assurer qu'un profil existe
    prof = getattr(request.user, 'profile', None)
    if prof is None:
        prof = Profile.objects.create(user=request.user)
    
    user_favorite_games = prof.favorite_games if hasattr(prof, 'favorite_games') else []
    
    context = {
        'game_choices': game_choices,
        'user_favorite_games': user_favorite_games,
        'user_profile': prof,
        'can_change_username': prof.can_change_username,
        'next_username_change_date': prof.next_username_change_date,
        'page_title': 'Paramètres - Blizz Gaming',
    }
    return render(request, 'settings.html', context)

@login_required
def verify_current_password(request):
    """Vue pour vérifier le mot de passe actuel"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            current_password = data.get('current_password', '')
            
            # Vérifier le mot de passe actuel
            from django.contrib.auth import authenticate
            user = authenticate(username=request.user.username, password=current_password)
            
            if user is not None:
                return JsonResponse({'success': True, 'message': 'Mot de passe correct'})
            else:
                return JsonResponse({'success': False, 'message': 'Mot de passe incorrect'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Données invalides'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def update_password(request):
    """Vue pour mettre à jour le mot de passe"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            current_password = data.get('current_password', '')
            new_password = data.get('new_password', '')
            confirm_password = data.get('confirm_password', '')
            
            # Validation des données
            if not current_password or not new_password or not confirm_password:
                return JsonResponse({'success': False, 'message': 'Tous les champs sont requis'})
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': 'Les mots de passe ne correspondent pas'})
            
            if len(new_password) < 8:
                return JsonResponse({'success': False, 'message': 'Le mot de passe doit contenir au moins 8 caractères'})
            
            # Vérifier le mot de passe actuel
            from django.contrib.auth import authenticate
            user = authenticate(username=request.user.username, password=current_password)
            
            if user is None:
                return JsonResponse({'success': False, 'message': 'Mot de passe actuel incorrect'})
            
            # Mettre à jour le mot de passe
            user.set_password(new_password)
            user.save()
            
            # Réauthentifier l'utilisateur pour éviter la déconnexion
            from django.contrib.auth import login
            login(request, user)
            
            return JsonResponse({'success': True, 'message': 'Mot de passe mis à jour avec succès'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Données invalides'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

def check_payment_setup(user):
    """
    Vérifie si un utilisateur a configuré et vérifié ses informations de paiement
    """
    try:
        payment_info = user.payment_info
        
        # Vérifier que les informations sont complètes
        has_complete_info = False
        if payment_info.preferred_payment_method == 'mobile_money':
            has_complete_info = bool(payment_info.phone_number and payment_info.operator)
        elif payment_info.preferred_payment_method == 'bank_transfer':
            has_complete_info = bool(payment_info.bank_name and payment_info.account_number and payment_info.account_holder_name)
        elif payment_info.preferred_payment_method == 'card':
            has_complete_info = bool(payment_info.card_number and payment_info.card_holder_name)
        
        # Vérifier que les informations sont vérifiées
        is_verified = payment_info.is_verified
        
        return has_complete_info and is_verified
    except Exception as e:
        return False

@login_required
@email_verified_required
def create(request):
    # Vérifier si l'utilisateur a configuré son paiement
    if not check_payment_setup(request.user):
        messages.error(request, 'Vous devez configurer vos informations de paiement avant de pouvoir créer une annonce.')
        return redirect('seller_payment_setup')
    
    # Importer CurrencyService au niveau global de la fonction
    from blizzgame.currency_service import CurrencyService
    
    if request.method == 'POST':
        title = request.POST.get('title', 'sans nom')
        caption = request.POST.get('caption', '')
        price = request.POST.get('price', '0')
        currency = request.POST.get('currency', 'XOF')
        game_type = request.POST.get('game', 'other')
        custom_game_name = request.POST.get('custom_game_name', '')
        coins = request.POST.get('coins', '')
        level = request.POST.get('level', '')
        banner = request.FILES.get('banner')
        
        # Upload de la bannière vers Cloudinary
        banner_cloudinary_url = None
        if banner:
            banner_cloudinary_url = upload_image_to_cloudinary(banner, 'post_banners')
        
        # Validation du prix et ajout de la commission de 10%
        try:
            price_value = float(price)
            
            # Prix minimums selon la devise (conversion approximative de 1000 FCFA ≈ 1.6 EUR)
            min_prices = {
                # Afrique de l'Ouest et Centrale
                'XOF': 1000, 'XAF': 1000, 'GNF': 15000, 'NGN': 1500, 'GHS': 20,
                # Maghreb
                'MAD': 16, 'DZD': 220, 'TND': 5.0, 'EGP': 55,
                # Afrique de l'Est et Australe
                'KES': 220, 'TZS': 4000, 'UGX': 6500, 'ZAR': 30, 'MUR': 75,
                # Devises principales
                'EUR': 1.6, 'USD': 1.8, 'GBP': 1.4,
                # Asie
                'JPY': 260, 'CNY': 13, 'INR': 150, 'KRW': 2400, 'THB': 60,
                'VND': 45000, 'IDR': 27000, 'PHP': 100, 'MYR': 8.0, 'SGD': 2.4,
                # Amérique
                'BRL': 9.0, 'MXN': 32, 'ARS': 1600, 'CLP': 1600, 'COP': 7500,
                'PEN': 6.0, 'UYU': 75, 'VES': 6500, 'CAD': 2.5, 'AUD': 2.7, 'NZD': 2.9,
                # Europe
                'CHF': 1.6, 'SEK': 18, 'NOK': 18, 'DKK': 12, 'PLN': 7.0, 'CZK': 40,
                'HUF': 620, 'RON': 8.0, 'BGN': 3.2, 'HRK': 12, 'RSD': 190,
                'UAH': 70, 'RUB': 160, 'TRY': 55
            }
            
            min_price = min_prices.get(currency, 100)
            
            # Vérifier le prix minimum AVANT d'ajouter la commission
            if price_value < min_price:
                currency_symbols = {
                    # Afrique
                    'XOF': 'FCFA', 'XAF': 'FCFA', 'GNF': 'GNF', 'NGN': '₦', 'GHS': '₵',
                    'MAD': 'د.م.', 'DZD': 'د.ج', 'TND': 'د.ت', 'EGP': 'ج.م',
                    'KES': 'KSh', 'TZS': 'TSh', 'UGX': 'USh', 'ZAR': 'R', 'MUR': '₨',
                    # Principales
                    'EUR': '€', 'USD': '$', 'GBP': '£',
                    # Asie
                    'JPY': '¥', 'CNY': '¥', 'INR': '₹', 'KRW': '₩', 'THB': '฿', 'VND': '₫',
                    'IDR': 'Rp', 'PHP': '₱', 'MYR': 'RM', 'SGD': 'S$',
                    # Amérique
                    'BRL': 'R$', 'MXN': '$', 'ARS': '$', 'CLP': '$', 'COP': '$',
                    'PEN': 'S/', 'UYU': '$', 'VES': 'Bs', 'CAD': 'CAD', 'AUD': 'A$', 'NZD': 'NZ$',
                    # Europe
                    'CHF': 'CHF', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr', 'PLN': 'zł', 'CZK': 'Kč',
                    'HUF': 'Ft', 'RON': 'lei', 'BGN': 'лв', 'HRK': 'kn', 'RSD': 'дин',
                    'UAH': '₴', 'RUB': '₽', 'TRY': '₺'
                }
                symbol = currency_symbols.get(currency, currency)
                messages.error(request, f'Le prix minimum est de {min_price} {symbol}.')
                return render(request, 'create.html', {
                    'currencies': CurrencyService.get_currencies_for_template(),
                    'current_currency': currency,
                    'payment_configured': check_payment_setup(request.user)
                })
            
            # ===== AJOUT AUTOMATIQUE DE LA COMMISSION DE 10% =====
            # Le vendeur reçoit le prix qu'il a fixé (price_value)
            # L'acheteur paie price_value + 10% de commission
            # Exemple: vendeur fixe 1000 FCFA → acheteur paie 1100 FCFA → vendeur reçoit 1000 FCFA (après payout)
            from decimal import Decimal
            price_with_commission = Decimal(str(price_value)) * Decimal('1.10')
            
            # Arrondir à 2 décimales
            price_with_commission = round(price_with_commission, 2)
            
            # Log pour le débogage
            logger.info(f"Prix fixé par le vendeur: {price_value} {currency}")
            logger.info(f"Prix avec commission (10%): {price_with_commission} {currency}")
            
            # Remplacer le prix par le prix avec commission
            price_value = float(price_with_commission)
            
            # Validation du prix maximum APRÈS ajout de la commission
            if price_value > 999999.99:
                messages.error(request, 'PRICE_TOO_HIGH')
                return render(request, 'create.html', {
                    'currencies': CurrencyService.get_currencies_for_template(),
                    'current_currency': currency,
                    'payment_configured': check_payment_setup(request.user)
                })
        except (ValueError, TypeError):
            messages.error(request, 'Prix invalide. Veuillez entrer un nombre valide.')
            return render(request, 'create.html', {
                'currencies': CurrencyService.get_currencies_for_template(),
                'current_currency': currency,
                'payment_configured': check_payment_setup(request.user)
            })
        
        # Convertir le prix vers EUR avant de le stocker
        # Tous les prix sont stockés en EUR dans la base de données
        try:
            if currency != 'EUR':
                price_in_eur = CurrencyService.convert_amount(price_value, currency, 'EUR')
                # Vérifier que le prix converti n'est pas trop élevé
                if price_in_eur > 999999.99:
                    messages.error(request, 'PRICE_CONVERSION_TOO_HIGH')
                    return render(request, 'create.html', {
                        'currencies': CurrencyService.get_currencies_for_template(),
                        'current_currency': currency,
                        'payment_configured': check_payment_setup(request.user)
                    })
            else:
                price_in_eur = price_value
        except Exception as e:
            messages.error(request, 'PRICE_CONVERSION_ERROR')
            return render(request, 'create.html', {
                'currencies': CurrencyService.get_currencies_for_template(),
                'current_currency': currency,
                'payment_configured': check_payment_setup(request.user)
            })
        
        # Créer le post avec tous les champs
        post = Post.objects.create(
            user=request.user.username,
            author=request.user,
            title=title,
            caption=caption,
            price=price_in_eur,  # Prix stocké en EUR
            game_type=game_type,
            custom_game_name=custom_game_name if game_type == 'other' else '',
            coins=coins,
            level=level,
            banner=banner if banner else 'def_img.png'
        )
        
        # Sauver l'URL Cloudinary de la bannière si disponible
        if banner_cloudinary_url:
            try:
                post.banner_url = banner_cloudinary_url
                post.save()
            except AttributeError:
                # Le champ n'existe pas encore, migration pas appliquée
                pass
        
        # Gérer les images supplémentaires
        images = request.FILES.getlist('images[]')
        for i, image in enumerate(images[:15]):  # Max 15 images
            # Upload vers Cloudinary
            image_cloudinary_url = upload_image_to_cloudinary(image, 'post_images')
            
            post_image = PostImage.objects.create(
                post=post,
                image=image,
                order=i
            )
            
            # Sauver l'URL Cloudinary si disponible
            if image_cloudinary_url:
                try:
                    post_image.image_url = image_cloudinary_url
                    post_image.save()
                except AttributeError:
                    # Le champ n'existe pas encore, migration pas appliquée
                    pass
        
        
        messages.success(request, 'Annonce créée avec succès!')
        return redirect('product_detail', post_id=post.id)
    
    # Utiliser XOF (FCFA) comme devise par défaut pour la création d'annonce
    from blizzgame.currency_service import CurrencyService
    current_currency = 'XOF'  # FCFA par défaut pour l'Afrique de l'Ouest
    current_currency_symbol = 'FCFA'  # Afficher le symbole au lieu du code
    
    # Vérifier l'état de configuration du paiement
    payment_configured = check_payment_setup(request.user)
    
    return render(request, 'create.html', {
        'currencies': CurrencyService.get_currencies_for_template(),
        'current_currency': current_currency,
        'current_currency_symbol': current_currency_symbol,
        'payment_configured': payment_configured,
        'page_title': 'Créer une annonce - Blizz Gaming'
    })

def product_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Vérifier si l'annonce est disponible
    if not post.is_on_sale and not post.is_sold and not post.is_in_transaction:
        messages.warning(request, "Cette annonce n'est plus disponible.")
        return redirect('index')
    
    # Récupérer les images et vidéos associées au post
    images = post.images.all().order_by('order')
    video = post.videos.first()  # Une seule vidéo par post
    
    # Récupérer le badge de réputation du vendeur
    seller_badge = None
    if hasattr(post.author, 'userreputation'):
        seller_badge = post.author.userreputation.get_seller_badge()
    else:
        # Si pas de UserReputation, utiliser Bronze I par défaut
        from .badge_config import get_seller_badge
        seller_badge = get_seller_badge(0.0, 0)  # Score 0, 0 transactions = Bronze I
    
    # Vérifier s'il existe déjà une transaction en cours entre l'utilisateur connecté et le vendeur
    existing_transaction = None
    if request.user.is_authenticated and request.user != post.author:
        existing_transaction = Transaction.objects.filter(
            buyer=request.user,
            seller=post.author,
            post=post,
            status__in=['pending', 'processing']
        ).first()
    
    context = {
        'post': post,
        'images': images,
        'video': video,
        'seller_badge': seller_badge,
        'existing_transaction': existing_transaction,
    }
    
    return render(request, 'product_detail.html', context)

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    post.delete()
    return redirect('index')

def logout_view(request):
    logout(request)
    return redirect('index')

from django_ratelimit.decorators import ratelimit
from django.core.cache import cache
import time

@ratelimit(key='ip', rate='5/m', method='POST', block=False)
@ratelimit(key='ip', rate='20/h', method='POST', block=False)
def signin(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    # Si la limite IP est atteinte, ne bloque pas mais ignore seulement l'incrément et continue
    rate_limited = getattr(request, 'limited', False)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Vérifier le verrouillage du compte
        lockout_key = f"lockout_{username}"
        if cache.get(lockout_key):
            remaining_time = cache.ttl(lockout_key)
            messages.error(request, f'Compte temporairement verrouillé. Réessayez dans {remaining_time} secondes.')
            return render(request, 'signin.html')
        
        if username and password:
            # Protection contre indisponibilité du cache/Redis
            try:
                cache_available = True
                _ = cache.get('healthcheck')
            except Exception:
                cache_available = False

            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Vérifier si l'utilisateur est banni
                try:
                    # Utiliser directement l'utilisateur authentifié
                    user_profile = user

                    # Récupérer les bannissements actifs (filtrer l'expiration côté Python
                    # pour éviter les erreurs de champ entre end_date/ends_at)
                    active_bans_qs = UserBan.objects.filter(
                        user=user_profile,
                        is_active=True
                    )

                    now_ts = timezone.now()
                    active_bans = []
                    for b in active_bans_qs:
                        ban_end = getattr(b, 'ends_at', getattr(b, 'end_date', None))
                        if ban_end and ban_end < now_ts:
                            continue
                        active_bans.append(b)

                    if active_bans:
                        # Récupérer le bannissement le plus récent par created_at si dispo sinon starts_at
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
                        
                        # Logger la tentative de connexion
                        logger.warning(f"Utilisateur banni {username} a tenté de se connecter")
                        
                        # Rediriger vers la page d'information sur le bannissement
                        return redirect('banned_user')
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la vérification du bannissement pour {username}: {e}")
                
                # Réinitialiser le compteur d'échecs
                if cache_available:
                    try:
                        cache.delete(f"failed_attempts_{username}")
                    except Exception:
                        pass
                login(request, user)
                messages.success(request, f'Bienvenue {username}!')
                return redirect('index')
            else:
                # Incrémenter le compteur d'échecs
                failed_attempts = 0
                if cache_available:
                    try:
                        failed_key = f"failed_attempts_{username}"
                        failed_attempts = cache.get(failed_key, 0) + 1
                        cache.set(failed_key, failed_attempts, 300)  # 5 minutes
                    except Exception:
                        failed_attempts = 0
                
                if failed_attempts >= 5 and cache_available and not rate_limited:
                    # Verrouiller le compte pendant 15 minutes
                    try:
                        cache.set(lockout_key, True, 900)
                    except Exception:
                        pass
                    messages.error(request, 'Trop de tentatives échouées. Compte verrouillé pendant 15 minutes.')
                else:
                    messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')
    
    return render(request, 'signin.html')

def signup(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        terms = request.POST.get('terms')
        
        if not all([username, email, password, password2, terms]):
            messages.error(request, 'Veuillez remplir tous les champs et accepter les conditions.')
            return render(request, 'signup.html')
        
        # Validation de la longueur du pseudo
        if len(username) < 3:
            messages.error(request, 'Le nom d\'utilisateur doit contenir au moins 3 caractères.')
            return render(request, 'signup.html')
        
        if password != password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return render(request, 'signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
            return render(request, 'signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé.')
            return render(request, 'signup.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Créer le profil utilisateur
            Profile.objects.create(user=user)
            
            # Créer la réputation utilisateur (pour le système d'insignes)
            UserReputation.objects.create(user=user)
            
            # Créer la vérification email
            email_verification = EmailVerification.objects.create(user=user)
            email_verification.send_verification_email()
            
            messages.success(request, f'Compte créé avec succès! Vérifiez votre email pour activer votre compte.')
            return redirect('signin')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du compte: {str(e)}')
    
    return render(request, 'signup.html')

# ===== Transactions gaming (stubs minimaux) =====

@login_required
def initiate_transaction(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Log pour déboguer
    logger.info(f"Initiation transaction pour annonce {post.id} par {request.user.username}")
    logger.info(f"Statut initial: is_on_sale={post.is_on_sale}, is_sold={post.is_sold}, is_in_transaction={post.is_in_transaction}")
    
    # Vérifier que l'annonce est disponible
    if post.is_sold:
        messages.error(request, "Cette annonce a déjà été vendue.")
        return redirect('index')
    
    # Vérifier que l'annonce n'est pas indisponible
    if not post.is_on_sale and not post.is_sold and not post.is_in_transaction:
        messages.error(request, "Cette annonce n'est plus disponible.")
        return redirect('index')
    
    # Vérifier que l'utilisateur n'achète pas sa propre annonce
    if request.user == post.author:
        messages.error(request, "Vous ne pouvez pas acheter votre propre annonce.")
        return redirect('index')
    
    # Vérifier s'il existe déjà une transaction en cours entre ces utilisateurs pour ce post
    existing_transaction = Transaction.objects.filter(
        buyer=request.user,
        seller=post.author,
        post=post,
        status__in=['pending', 'processing', 'disputed']
    ).first()
    
    if existing_transaction:
        # Rediriger vers la transaction existante
        logger.info(f"Transaction existante trouvée pour {post.title}: {existing_transaction.id}")
        messages.info(request, f"Vous avez déjà une transaction en cours pour {post.title}.")
        return redirect('transaction_detail', transaction_id=existing_transaction.id)
    
    # Vérifier si l'annonce est déjà en transaction avec quelqu'un d'autre
    if post.is_in_transaction:
        messages.error(request, "Cette annonce est actuellement en cours de transaction avec un autre utilisateur.")
        return redirect('index')
    
    # Créer la transaction avec statut 'pending' (en attente de paiement)
    transaction = Transaction.objects.create(
        buyer=request.user, 
        seller=post.author, 
        post=post, 
        amount=post.price,
        status='pending'  # Changé de 'processing' à 'pending'
    )
    
    # NE PAS mettre à jour le statut de l'annonce maintenant
    # L'annonce restera disponible jusqu'à ce que le paiement soit confirmé
    # post.is_in_transaction = True
    # post.is_on_sale = False
    # post.save()
    
    # ===== NOTIFICATION POUR LE VENDEUR =====
    from .models import Notification
    Notification.objects.create(
        user=post.author,  # Le vendeur
        type='transaction_started',
        title='🎉 Nouvelle vente !',
        content=f"Un acheteur a initié une transaction pour votre annonce '{post.title}' d'une valeur de {post.price} EUR. La transaction est en attente de paiement.",
        transaction=transaction
    )
    
    # Log pour déboguer
    logger.info(f"Annonce {post.id} mise à jour: is_in_transaction={post.is_in_transaction}, is_on_sale={post.is_on_sale}")
    logger.info(f"Notification créée pour le vendeur {post.author.username} pour la transaction {transaction.id}")
    
    messages.success(request, f"Transaction initiée pour {post.title}. Vous pouvez maintenant procéder au paiement.")
    return redirect('transaction_detail', transaction_id=transaction.id)

@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Log pour debug
    logger.info(f"Accès transaction {transaction_id} par {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    logger.info(f"Acheteur: {transaction.buyer.username}, Vendeur: {transaction.seller.username}")
    
    # Vérifier l'authentification (double vérification pour les retours CinetPay)
    if not request.user.is_authenticated:
        logger.warning(f"Utilisateur non authentifié tente d'accéder à la transaction {transaction_id}")
        messages.warning(request, "Veuillez vous connecter pour accéder à cette transaction.")
        return redirect(f'/signin/?next=/transaction/{transaction_id}/')
    
    # Vérifier si l'utilisateur est impliqué dans cette transaction (ou admin)
    if request.user != transaction.buyer and request.user != transaction.seller and not request.user.is_staff:
        logger.warning(f"Accès refusé à la transaction {transaction_id} pour {request.user.username}")
        messages.error(request, "Vous n'avez pas accès à cette transaction.")
        return redirect('index')
    
    # Déterminer le rôle de l'utilisateur
    is_buyer = request.user == transaction.buyer
    
    # Vérifier s'il y a un litige ouvert pour cette transaction
    has_open_dispute = Dispute.objects.filter(
        transaction=transaction,
        status__in=['pending', 'in_progress']
    ).exists()
    
    # Vérifier si le paiement CinetPay est validé
    cinetpay_payment_validated = False
    if hasattr(transaction, 'cinetpay_transaction'):
        cinetpay_payment_validated = transaction.cinetpay_transaction.status in ['payment_received', 'in_escrow', 'escrow_released', 'completed']
    
    # Déterminer si le chat doit être activé
    # Le chat n'est activé que si le paiement CinetPay est validé ET qu'il n'y a pas de litige ouvert
    chat_enabled = cinetpay_payment_validated and not has_open_dispute
    
    # S'assurer que l'annonce a le bon statut selon la transaction
    post = transaction.post
    if transaction.status == 'disputed' and post.is_on_sale:
        # Si la transaction est en litige mais l'annonce est encore en vente, corriger
        post.is_on_sale = False
        post.is_in_transaction = False
        post.is_sold = False
        post.save()
        logger.info(f"Annonce {post.id} corrigée: marquée comme indisponible pour litige")
    elif transaction.status == 'processing' and not post.is_in_transaction:
        # Si la transaction est en cours mais l'annonce n'est pas marquée en transaction
        post.is_in_transaction = True
        post.is_on_sale = False
        post.save()
        logger.info(f"Annonce {post.id} corrigée: marquée comme en transaction")
    elif transaction.status == 'completed' and not post.is_sold:
        # Si la transaction est terminée mais l'annonce n'est pas marquée comme vendue
        post.is_sold = True
        post.is_in_transaction = False
        post.is_on_sale = False
        post.save()
        logger.info(f"Annonce {post.id} corrigée: marquée comme vendue")
    elif transaction.status == 'failed' and post.is_in_transaction:
        # Si la transaction a échoué mais l'annonce est encore marquée en transaction
        post.is_in_transaction = False
        post.is_on_sale = True
        post.is_sold = False
        post.save()
        logger.info(f"Annonce {post.id} corrigée: remise en vente après échec de transaction")
    elif transaction.status == 'cancelled' and post.is_in_transaction:
        # Si la transaction est annulée mais l'annonce est encore marquée en transaction
        post.is_in_transaction = False
        post.is_on_sale = True
        post.is_sold = False
        post.save()
        logger.info(f"Annonce {post.id} corrigée: remise en vente après annulation de transaction")
    
    # Le chat_enabled est déjà défini plus haut
    
    # Intégration du nouveau système de chat Django Channels
    chat = None
    chat_messages = []
    chat_locked = True
    websocket_url = None
    
    # Toujours récupérer ou créer le chat, même s'il est verrouillé
    try:
        chat, created = Chat.objects.get_or_create(
            transaction=transaction,
            defaults={
                'is_active': True,
                'is_locked': False
            }
        )
        
        # Mettre à jour le statut de blocage selon le statut de la transaction
        chat.is_locked = transaction.status not in ['processing']
        chat.save()
        
        # Récupérer les messages de chat
        chat_messages = Message.objects.filter(chat=chat).order_by('created_at')
        
        # Marquer les messages comme lus seulement si le chat est activé
        if chat_enabled:
            Message.objects.filter(chat=chat, is_read=False).exclude(sender=request.user).update(is_read=True)
        
        # URL WebSocket
        websocket_url = f'ws://{request.get_host()}/ws/chat/transaction/{transaction_id}/'
        
    except Exception as e:
        print(f"Erreur lors de la création/récupération du chat: {e}")
        chat = None
        chat_messages = []
        chat_locked = True
    
    # Vérifier si on est dans la période de sécurité (24h après création)
    from datetime import timedelta
    security_period = timedelta(hours=24)
    time_since_creation = timezone.now() - transaction.created_at
    in_security_period = time_since_creation < security_period
    
    context = {
        'transaction': transaction,
        'is_buyer': is_buyer,
        'cinetpay_payment_validated': cinetpay_payment_validated,
        'chat_enabled': chat_enabled,
        'has_open_dispute': has_open_dispute,
        'chat': chat,
        'chat_messages': chat_messages,
        'chat_locked': chat.is_locked if chat else True,
        'websocket_url': websocket_url,
        'other_user': transaction.seller if is_buyer else transaction.buyer,
        'in_security_period': in_security_period,
    }
    
    # Utiliser le template AJAX pour éviter les problèmes WebSocket
    return render(request, 'transaction_detail_ajax.html', context)

@login_required
def transaction_list(request):
    purchases = Transaction.objects.filter(buyer=request.user).order_by('-created_at')
    sales = Transaction.objects.filter(seller=request.user).order_by('-created_at')
    
    context = {
        'purchases': purchases,
        'sales': sales,
    }
    return render(request, 'transactions.html', context)

@login_required
def confirm_reception(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, buyer=request.user)
    
    if transaction.status == 'processing':
        from django.utils import timezone
        from decimal import Decimal
        from .models import EscrowTransaction, PayoutRequest, SellerPaymentInfo
        
        transaction.status = 'completed'
        transaction.completed_at = timezone.now()
        transaction.save()
        
        # ===== CRÉATION DU PAYOUT =====
        payout_message = ""
        try:
            # Vérifier si la transaction a un paiement CinetPay associé
            if hasattr(transaction, 'cinetpay_transaction'):
                # Vérifier si le vendeur a des informations de paiement
                try:
                    seller_payment_info = SellerPaymentInfo.objects.get(
                        user=transaction.seller,
                        is_verified=True
                    )
                    
                    # ===== CALCUL DU MONTANT VENDEUR =====
                    # Le prix stocké (transaction.amount) inclut déjà la commission de 10%
                    # Pour obtenir le montant que le vendeur doit recevoir (ce qu'il a fixé),
                    # on divise par 1.10 au lieu de multiplier par 0.90
                    # Exemple: Prix avec commission = 1100 FCFA
                    # → Montant vendeur = 1100 / 1.10 = 1000 FCFA ✅
                    seller_amount = transaction.amount / Decimal('1.10')
                    seller_amount = seller_amount.quantize(Decimal('0.01'))  # Arrondir à 2 décimales
                    
                    # Créer un EscrowTransaction si il n'existe pas
                    escrow_transaction, created = EscrowTransaction.objects.get_or_create(
                        cinetpay_transaction=transaction.cinetpay_transaction,
                        defaults={
                            'amount': seller_amount,  # Montant exact pour le vendeur
                            'currency': 'EUR',
                            'status': 'in_escrow'
                        }
                    )
                    
                    # Déterminer les informations de réception
                    recipient_phone = seller_payment_info.phone_number
                    recipient_country = seller_payment_info.country
                    recipient_operator = seller_payment_info.operator
                    
                    # Créer un PayoutRequest
                    payout_request = PayoutRequest.objects.create(
                        escrow_transaction=escrow_transaction,
                        payout_type='seller_payout',
                        amount=seller_amount,  # Montant exact pour le vendeur (sans commission)
                        currency='EUR',
                        recipient_phone=recipient_phone,
                        recipient_country=recipient_country,
                        recipient_operator=recipient_operator,
                        status='pending'
                    )
                    
                    payout_message = f"Payout créé avec succès (ID: {str(payout_request.id)[:8]}) - En attente de validation manuelle"
                    logger.info(f"PayoutRequest créé pour la transaction {transaction.id}: {payout_request.id}")
                    
                except SellerPaymentInfo.DoesNotExist:
                    payout_message = "Payout en attente - Le vendeur doit configurer ses informations de paiement"
                    logger.warning(f"Vendeur {transaction.seller.username} n'a pas d'informations de paiement configurées")
            else:
                payout_message = "Payout en attente - Aucun paiement CinetPay associé"
                logger.warning(f"Transaction {transaction.id} n'a pas de paiement CinetPay associé")
                
        except Exception as e:
            logger.error(f"Erreur lors de la création du payout: {e}")
            payout_message = f"Erreur lors de la création du payout: {str(e)}"
        
        # Mettre à jour le statut de l'annonce - la marquer comme vendue
        post = transaction.post
        post.is_sold = True
        post.is_in_transaction = False
        post.is_on_sale = False
        post.save()
        logger.info(f"Annonce {post.id} marquée comme vendue après confirmation de réception")
        
        # Supprimer les médias de l'annonce vendue pour économiser l'espace
        from .media_cleanup import delete_post_media
        cleanup_result = delete_post_media(post)
        if cleanup_result['success']:
            logger.info(f"Médias supprimés pour l'annonce {post.id}: {cleanup_result['count']} fichiers")
        else:
            logger.error(f"Erreur lors de la suppression des médias pour l'annonce {post.id}: {cleanup_result['error']}")
        
        # Créer une notification pour le vendeur
        Notification.objects.create(
            user=transaction.seller,
            type='transaction_update',
            title='Réception confirmée',
            content=f"L'acheteur a confirmé la réception de {transaction.post.title}. {payout_message}",
            transaction=transaction
        )
        
        messages.success(request, f'Transaction confirmée avec succès! {payout_message}')
    
    return redirect('transaction_detail', transaction_id=transaction.id)

@login_required
def complete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Vérifier que l'utilisateur est l'acheteur
    if request.user != transaction.buyer:
        messages.error(request, "Vous n'êtes pas autorisé à effectuer cette action.")
        return redirect('transaction_detail', transaction_id=transaction.id)
    
    # Vérifier que le paiement est validé (en mode test gaming, on peut passer cette vérification)
    # Vérifier que le paiement est validé
    if not (hasattr(transaction, 'cinetpay_transaction') and 
            transaction.cinetpay_transaction.status in ['payment_received', 'in_escrow']):
        messages.error(request, "Le paiement doit être validé avant de confirmer la réception.")
        return redirect('transaction_detail', transaction_id=transaction.id)
    
    if transaction.status in ['processing', 'pending', 'disputed']:
        transaction.status = 'completed'
        transaction.save()
        
        # Mettre à jour le statut CinetPay vers "escrow_released"
        if hasattr(transaction, 'cinetpay_transaction'):
            transaction.cinetpay_transaction.status = 'escrow_released'
            transaction.cinetpay_transaction.save()
        
        # CRÉER UN PAYOUT REQUEST POUR LE VENDEUR
        try:
            # Vérifier que le vendeur a des informations de paiement configurées
            try:
                seller_payment_info = transaction.seller.payment_info
                if not seller_payment_info.is_verified:
                    payout_message = "Payout en attente - Le vendeur doit configurer ses informations de paiement"
                    logger.warning(f"Vendeur {transaction.seller.username} n'a pas d'informations de paiement vérifiées")
                else:
                    # Créer un EscrowTransaction si il n'existe pas
                    escrow_transaction, created = EscrowTransaction.objects.get_or_create(
                        cinetpay_transaction=transaction.cinetpay_transaction,
                        defaults={
                            'amount': transaction.amount * Decimal('0.9'),  # 90% pour le vendeur
                            'currency': 'EUR',
                            'status': 'in_escrow'
                        }
                    )
                    
                    # Déterminer les informations de réception selon la méthode préférée
                    recipient_phone = seller_payment_info.phone_number
                    recipient_country = seller_payment_info.country
                    recipient_operator = seller_payment_info.operator
                    
                    # Créer un PayoutRequest
                    payout_request = PayoutRequest.objects.create(
                        escrow_transaction=escrow_transaction,
                        amount=transaction.amount * Decimal('0.9'),  # 90% pour le vendeur
                        currency='EUR',
                        recipient_phone=recipient_phone,
                        recipient_country=recipient_country,
                        recipient_operator=recipient_operator,
                        status='pending'
                    )
                    
                    payout_message = f"Payout créé avec succès (ID: {str(payout_request.id)[:8]}) - En attente de validation manuelle"
                    logger.info(f"PayoutRequest créé pour la transaction {transaction.id}: {payout_request.id}")
            except SellerPaymentInfo.DoesNotExist:
                payout_message = "Payout en attente - Le vendeur doit configurer ses informations de paiement"
                logger.warning(f"Vendeur {transaction.seller.username} n'a pas d'informations de paiement configurées")
                
        except Exception as e:
            logger.error(f"Erreur lors de la création du payout: {e}")
            payout_message = f"Erreur lors de la création du payout: {str(e)}"
        
        # Marquer l'annonce comme vendue
        post = transaction.post
        post.is_sold = True
        post.is_in_transaction = False
        post.is_on_sale = False
        post.save()
        
        # Log pour déboguer
        logger.info(f"Transaction {transaction.id} complétée, annonce {post.id} marquée comme vendue")
        
        # Créer une notification pour le vendeur
        Notification.objects.create(
            user=transaction.seller,
            type='transaction_update',
            title='Fonds libérés',
            content=f"L'acheteur a confirmé la réception de {transaction.post.title}. {payout_message}",
            transaction=transaction
        )
        
        messages.success(request, f'Transaction complétée avec succès! {payout_message}')
    else:
        messages.error(request, 'Cette transaction ne peut pas être complétée dans son état actuel.')
    
    return redirect('transaction_detail', transaction_id=transaction.id)

@login_required
def dispute_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Vérifier que l'utilisateur est impliqué dans la transaction
    if request.user not in [transaction.buyer, transaction.seller]:
        messages.error(request, "Vous n'êtes pas autorisé à effectuer cette action.")
        return redirect('transaction_detail', transaction_id=transaction.id)
    
    # Vérifier que la transaction peut être disputée
    if transaction.status not in ['processing', 'pending']:
        messages.error(request, "Cette transaction ne peut plus être disputée.")
        return redirect('transaction_detail', transaction_id=transaction.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        description = request.POST.get('description', '')
        
        if not reason or not description:
            messages.error(request, "Veuillez fournir une raison et une description du litige.")
            return redirect('transaction_detail', transaction_id=transaction.id)
        
        # Créer le litige dans la base de données
        dispute = Dispute.objects.create(
            transaction=transaction,
            opened_by=request.user,
            reason=reason,
            description=description,
            disputed_amount=transaction.amount,
            deadline=timezone.now() + timezone.timedelta(hours=72),  # 72h pour résolution
            evidence={}  # Initialiser avec un dictionnaire vide valide
        )
        
        # Mettre à jour le statut de la transaction
        transaction.status = 'disputed'
        transaction.save()
        
        # Mettre à jour le statut de l'annonce - la marquer comme indisponible pendant le litige
        post = transaction.post
        post.is_in_transaction = False  # Plus en transaction
        post.is_sold = False  # Pas encore vendue
        post.is_on_sale = False  # Indisponible à la vente pendant le litige
        post.save()
        
        # Créer les notifications automatiques
        create_dispute_notification(dispute)
        
        messages.success(request, 'Litige créé avec succès. Notre équipe va examiner votre demande dans les 72h.')
        return redirect('transaction_detail', transaction_id=transaction.id)
    
    # Afficher le formulaire de litige
    return render(request, 'dispute_form.html', {'transaction': transaction})

@login_required
def send_transaction_message(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Vérifier que l'utilisateur est impliqué dans cette transaction
    if request.user != transaction.buyer and request.user != transaction.seller:
        return JsonResponse({'status': 'error', 'message': 'Accès non autorisé'})
    
    # Vérifier que le chat est autorisé (processing ou paiement validé)
    chat_allowed = False
    
    # Chat autorisé si transaction en processing
    if transaction.status == 'processing':
        chat_allowed = True
    # Ou si paiement CinetPay validé
    elif hasattr(transaction, 'cinetpay_transaction'):
        chat_allowed = transaction.cinetpay_transaction.status in ['payment_received', 'in_escrow', 'escrow_released', 'completed']
    
    if not chat_allowed:
        return JsonResponse({'status': 'error', 'message': 'Chat verrouillé - paiement requis'})
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'status': 'error', 'message': 'Message vide'})
        
        # Créer ou récupérer le chat de transaction
        chat, created = Chat.objects.get_or_create(
            transaction=transaction
        )
        
        # Créer le message de transaction
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=content
        )
        
        # Envoyer le message via Pusher
        try:
            from blizzgame.pusher_config import send_message_to_chat, send_notification_to_user
            message_data = {
                'content': message.content,
                'sender_id': str(message.sender.id),
                'sender_username': message.sender.username,
                'created_at': message.created_at.strftime('%H:%M')
            }
            send_message_to_chat(transaction_id, message_data)
            
            # Créer ou mettre à jour une notification groupée
            recipient = transaction.seller if request.user == transaction.buyer else transaction.buyer
            notification = create_or_update_message_notification(message, recipient)
            
            # Envoyer une notification en temps réel au destinataire
            send_notification_to_user(recipient.id, {
                'title': 'Nouveau message',
                'message': f'Nouveau message de {message.sender.username}',
                'count': Notification.objects.filter(user=recipient, is_read=False).count()
            })
        except Exception as e:
            print(f"Erreur Pusher: {e}")
        
        # Toujours retourner JSON (pas de redirection)
        return JsonResponse({
            'status': 'success',
            'message': {
                'content': message.content,
                'sender': message.sender.username,
                'created_at': message.created_at.strftime('%H:%M')
            }
        })
    
    # Si ce n'est pas une requête POST, retourner une erreur JSON
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'})

@login_required
def get_transaction_messages(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Vérifier que l'utilisateur est impliqué dans cette transaction
    if request.user != transaction.buyer and request.user != transaction.seller:
        return JsonResponse({'status': 'error', 'message': 'Accès non autorisé'})
    
    # Récupérer les messages de transaction
    chat = Chat.objects.filter(transaction=transaction).first()
    
    messages_data = []
    if chat:
        messages_list = chat.messages.select_related('sender').order_by('created_at')
        messages_data = [{
            'content': msg.content,
            'sender': msg.sender.username,
            'created_at': msg.created_at.strftime('%H:%M'),
            'is_mine': msg.sender == request.user
        } for msg in messages_list]
    
    return JsonResponse({'messages': messages_data})

# ===== CinetPay pour transactions gaming existantes (stubs) =====

@login_required
def initiate_cinetpay_payment(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Log de démarrage pour forcer le redémarrage
    print(f"[CINETPAY START] Transaction {transaction_id} - Montant: {transaction.amount}")
    logger.error(f"[CINETPAY START] Transaction {transaction_id} - Montant: {transaction.amount}")
    
    # Mode production - pas de simulation
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            customer_name = request.POST.get('customer_name')
            customer_surname = request.POST.get('customer_surname')
            customer_email = request.POST.get('customer_email')
            
            # Combiner le code pays et le numéro de téléphone
            phone_country_code = request.POST.get('customer_phone_country_code', '')
            phone_number = request.POST.get('customer_phone_number', '')
            customer_phone_number = phone_country_code + phone_number if phone_country_code and phone_number else request.POST.get('customer_phone_number', '')
            
            customer_address = request.POST.get('customer_address')
            customer_city = request.POST.get('customer_city')
            customer_zip_code = request.POST.get('customer_zip_code')
            customer_country = request.POST.get('customer_country')
            customer_state = request.POST.get('customer_state')
            
            # Rediriger les pays non-africains vers le Sénégal pour CinetPay
            african_countries = ['CI', 'SN', 'BF', 'ML', 'NE', 'TG', 'BJ', 'GN', 'CM', 'CD', 'CDUSD']
            if customer_country and customer_country not in african_countries:
                # Pays non-africain - utiliser le Sénégal pour CinetPay
                logger.info(f"Pays {customer_country} redirigé vers le Sénégal pour CinetPay")
                customer_country = 'SN'  # Sénégal
            
            # Log des données reçues pour débogage
            print(f"[CINETPAY DEBUG] Données reçues - Name: '{customer_name}', Surname: '{customer_surname}', Email: '{customer_email}', Phone: '{customer_phone_number}'")
            logger.error(f"[CINETPAY DEBUG] Données reçues - Name: '{customer_name}', Surname: '{customer_surname}', Email: '{customer_email}', Phone: '{customer_phone_number}'")
            
            # Appliquer des valeurs par défaut robustes pour éviter MINIMUM_REQUIRED_FIELDS côté CinetPay
            if not customer_name:
                customer_name = getattr(request.user, 'first_name', '') or 'Gamer'
                logger.info(f"[CINETPAY DEBUG] customer_name vide, fallback: '{customer_name}'")
            if not customer_surname:
                customer_surname = getattr(request.user, 'last_name', '') or 'BLIZZ'
                logger.info(f"[CINETPAY DEBUG] customer_surname vide, fallback: '{customer_surname}'")
            if not customer_email:
                customer_email = getattr(request.user, 'email', '') or 'gamer@blizz.com'
                logger.info(f"[CINETPAY DEBUG] customer_email vide, fallback: '{customer_email}'")
            if not customer_phone_number:
                customer_phone_number = '+221701234567'
                logger.info(f"[CINETPAY DEBUG] customer_phone_number vide, fallback: '{customer_phone_number}'")
            if not customer_address:
                customer_address = 'Adresse non renseignée'
                logger.info(f"[CINETPAY DEBUG] customer_address vide, fallback: '{customer_address}'")
            if not customer_city:
                customer_city = 'Dakar'
                logger.info(f"[CINETPAY DEBUG] customer_city vide, fallback: '{customer_city}'")
            if not customer_zip_code:
                customer_zip_code = '12345'
                logger.info(f"[CINETPAY DEBUG] customer_zip_code vide, fallback: '{customer_zip_code}'")
            if not customer_country:
                customer_country = 'SN'
                logger.info(f"[CINETPAY DEBUG] customer_country vide, fallback: '{customer_country}'")
            if not customer_state:
                customer_state = 'Dakar'
                logger.info(f"[CINETPAY DEBUG] customer_state vide, fallback: '{customer_state}'")
            
            # Log des données finales
            print(f"[CINETPAY DEBUG] Données finales - Name: '{customer_name}', Surname: '{customer_surname}', Email: '{customer_email}', Phone: '{customer_phone_number}'")
            logger.error(f"[CINETPAY DEBUG] Données finales - Name: '{customer_name}', Surname: '{customer_surname}', Email: '{customer_email}', Phone: '{customer_phone_number}'")

            # Revalidation post-fallback (devrait toujours passer)
            required_fields = {
                'customer_name': customer_name,
                'customer_surname': customer_surname,
                'customer_email': customer_email,
                'customer_phone_number': customer_phone_number,
                'customer_address': customer_address,
                'customer_city': customer_city,
                'customer_zip_code': customer_zip_code,
                'customer_country': customer_country,
                'customer_state': customer_state,
            }
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                return JsonResponse({
                    'success': False,
                    'error': f'Champs requis manquants: {", ".join(missing_fields)}'
                })
            
            # Calculer la commission (10%) et le montant vendeur (90%)
            amount = float(transaction.amount)
            platform_commission = amount * 0.10
            seller_amount = amount * 0.90
            
            # Convertir selon la devise de l'utilisateur
            user_currency = CurrencyService.get_user_currency(request.user)
            if user_currency != 'EUR':
                # Convertir les montants vers la devise de l'utilisateur pour l'affichage
                amount = CurrencyService.convert_amount(amount, 'EUR', user_currency)
                platform_commission = CurrencyService.convert_amount(platform_commission, 'EUR', user_currency)
                seller_amount = CurrencyService.convert_amount(seller_amount, 'EUR', user_currency)
            
            # Récupérer les données de paiement du vendeur
            seller = transaction.seller
            seller_phone = None
            seller_country = None
            seller_operator = None
            
            if hasattr(seller, 'payment_info') and check_payment_setup(seller):
                payment_info = seller.payment_info
                if payment_info.preferred_payment_method == 'mobile_money':
                    seller_phone = payment_info.phone_number
                    seller_country = payment_info.country
                    seller_operator = payment_info.operator
                else:
                    # Pour les autres méthodes, utiliser des valeurs par défaut
                    seller_phone = customer_phone_number
                    seller_country = customer_country
                    seller_operator = 'ORANGE'
            else:
                # Fallback si pas de configuration
                seller_phone = customer_phone_number
                seller_country = customer_country
                seller_operator = 'ORANGE'
            
            # Créer ou mettre à jour la transaction CinetPay avec gestion de transaction
            from django.db import transaction as db_transaction
            
            with db_transaction.atomic():
                cinetpay_transaction, created = CinetPayTransaction.objects.get_or_create(
                    transaction=transaction,
                    defaults={
                        'amount': amount,
                        'currency': 'EUR',
                        'platform_commission': platform_commission,
                        'seller_amount': seller_amount,
                        'customer_name': customer_name,
                        'customer_surname': customer_surname,
                        'customer_email': customer_email,
                        'customer_phone_number': customer_phone_number,
                        'customer_address': customer_address,
                        'customer_city': customer_city,
                        'customer_zip_code': customer_zip_code,
                        'customer_country': customer_country,
                        'customer_state': customer_state,
                        'seller_phone_number': seller_phone,
                        'seller_country': seller_country,
                        'seller_operator': seller_operator,
                        'cinetpay_transaction_id': f'BLIZZ_{transaction.id}_{timezone.now().strftime("%Y%m%d%H%M%S")}',
                        'status': 'pending_payment'
                    }
                )
            
            if not created:
                # Mettre à jour les informations si la transaction existe déjà avec gestion de transaction
                with db_transaction.atomic():
                    cinetpay_transaction.amount = amount
                    cinetpay_transaction.platform_commission = platform_commission
                    cinetpay_transaction.seller_amount = seller_amount
                    cinetpay_transaction.customer_name = customer_name
                    cinetpay_transaction.customer_surname = customer_surname
                    cinetpay_transaction.customer_email = customer_email
                    cinetpay_transaction.customer_phone_number = customer_phone_number
                    cinetpay_transaction.customer_address = customer_address
                    cinetpay_transaction.customer_city = customer_city
                    cinetpay_transaction.customer_zip_code = customer_zip_code
                    cinetpay_transaction.customer_country = customer_country
                    cinetpay_transaction.customer_state = customer_state
                    cinetpay_transaction.seller_phone_number = customer_phone_number
                    cinetpay_transaction.seller_country = customer_country
                    cinetpay_transaction.seller_operator = 'ORANGE'
                    cinetpay_transaction.save()
            
            # INITIER LE VRAI PAIEMENT CINETPAY
            from .cinetpay_utils import GamingCinetPayAPI
            
            # Créer l'instance de l'API CinetPay Gaming
            cinetpay_api = GamingCinetPayAPI()
            
            # Préparer les données client pour CinetPay
            customer_data = {
                'customer_name': customer_name,
                'customer_surname': customer_surname,
                'customer_email': customer_email,
                'customer_phone_number': customer_phone_number,
                'customer_address': customer_address,
                'customer_city': customer_city,
                'customer_zip_code': customer_zip_code,
                'customer_country': customer_country,
                'customer_state': customer_state,
            }
            
            # Initier le paiement via l'API CinetPay avec gestion de transaction
            from django.db import transaction as db_transaction
            
            with db_transaction.atomic():
                payment_result = cinetpay_api.initiate_payment(transaction, customer_data)
            
            if payment_result.get('success'):
                # Paiement initié avec succès - rediriger vers CinetPay
                payment_url = payment_result.get('payment_url')
                transaction_id = payment_result.get('transaction_id')
                
                logger.info(f"Paiement CinetPay initié avec succès: {transaction_id}")
            
                return JsonResponse({
                    'success': True,
                    'redirect_url': payment_url,  # Redirection vers CinetPay
                    'message': 'Redirection vers CinetPay...',
                    'payment_url': payment_url,
                    'transaction_id': transaction_id
                })
            else:
                # Erreur lors de l'initiation du paiement
                error_message = payment_result.get('error', 'Erreur lors de l\'initiation du paiement')
                logger.error(f"Erreur CinetPay: {error_message}")
                
                return JsonResponse({
                    'success': False,
                    'error': error_message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors du traitement: {str(e)}'
            })
    
    return render(request, 'cinetpay_payment_form.html', {'transaction': transaction})

@csrf_exempt
def gaming_cinetpay_notification(request):
    """
    Webhook pour recevoir les notifications CinetPay des transactions gaming
    """
    if request.method == 'POST':
        try:
            notification_data = json.loads(request.body)
            from .cinetpay_utils import handle_gaming_cinetpay_notification
            
            success = handle_gaming_cinetpay_notification(notification_data)
            
            if success:
                return HttpResponse('OK', status=200)
            else:
                return HttpResponse('Error processing notification', status=400)
        except Exception as e:
            logger.error(f"Erreur notification CinetPay Gaming: {e}")
            return HttpResponse('Error', status=500)
    return HttpResponse('Method not allowed', status=405)

@csrf_exempt
def cinetpay_notification(request):
    return HttpResponse('OK', status=200)

def cinetpay_payment_page(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    cinetpay_transaction = get_object_or_404(CinetPayTransaction, transaction=transaction)
    
    context = {
        'transaction_id': transaction.id,
        'amount': transaction.amount,
        'cinetpay_transaction': cinetpay_transaction
    }
    return render(request, 'cinetpay_payment_page.html', context)

@csrf_exempt
def cinetpay_payment_success(request, transaction_id):
    try:
        # Log pour déboguer
        logger.info(f"Tentative de traitement du paiement CinetPay pour la transaction {transaction_id}")
        
        # Vérifier si la transaction existe
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            logger.info(f"Transaction trouvée: {transaction.id}, statut: {transaction.status}")
        except Transaction.DoesNotExist:
            logger.error(f"Transaction {transaction_id} non trouvée dans la base de données")
            # Rediriger vers une page d'erreur ou la page d'accueil
            messages.error(request, f"Transaction {transaction_id} introuvable. Veuillez contacter le support.")
            return redirect('index')
        
        # Mettre à jour les statuts
        transaction.status = 'processing'
        transaction.save()
        logger.info(f"Transaction {transaction_id} mise à jour avec le statut 'processing'")
        
        # Mettre à jour le statut CinetPay
        if hasattr(transaction, 'cinetpay_transaction'):
            transaction.cinetpay_transaction.status = 'payment_received'
            transaction.cinetpay_transaction.payment_received_at = timezone.now()
            transaction.cinetpay_transaction.save()
            logger.info(f"Transaction CinetPay {transaction.cinetpay_transaction.id} mise à jour")
        else:
            logger.warning(f"Aucune transaction CinetPay associée à la transaction {transaction_id}")
        
        return render(request, 'cinetpay_success.html', {'transaction': transaction})
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du paiement CinetPay pour {transaction_id}: {e}")
        messages.error(request, "Une erreur est survenue lors du traitement de votre paiement. Veuillez contacter le support.")
        return redirect('index')

@csrf_exempt
def cinetpay_payment_failed(request, transaction_id):
    try:
        # Log pour déboguer
        logger.info(f"Tentative de traitement de l'échec de paiement CinetPay pour la transaction {transaction_id}")
        
        # Vérifier si la transaction existe
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            logger.info(f"Transaction trouvée: {transaction.id}, statut: {transaction.status}")
        except Transaction.DoesNotExist:
            logger.error(f"Transaction {transaction_id} non trouvée dans la base de données")
            messages.error(request, f"Transaction {transaction_id} introuvable. Veuillez contacter le support.")
            return redirect('index')
        
        transaction.status = 'failed'
        transaction.save()
        logger.info(f"Transaction {transaction_id} marquée comme échouée")

        # Remettre l'annonce en vente
        post = transaction.post
        post.is_in_transaction = False
        post.is_on_sale = True
        post.is_sold = False
        post.save()

        logger.info(f"Transaction {transaction_id} échouée - annonce {post.id} remise en vente")

        return render(request, 'cinetpay_failed.html', {'transaction': transaction})
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'échec de paiement CinetPay pour {transaction_id}: {e}")
        messages.error(request, "Une erreur est survenue lors du traitement de votre paiement. Veuillez contacter le support.")
        return redirect('index')

# ===== Chat, notifications et amis (stubs basiques pour éviter les erreurs d'import) =====

def chat_home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Récupérer les conversations privées de l'utilisateur
    private_conversations = PrivateConversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user),
        is_active=True
    ).select_related('user1', 'user2').order_by('-last_message_at')[:10]
    
    # Préparer les données des conversations
    conversations_data = []
    for conv in private_conversations:
        other_user = conv.user2 if conv.user1 == request.user else conv.user1
        last_message = conv.private_messages.order_by('-created_at').first()
        
        conversations_data.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': conv.private_messages.filter(
                is_read=False
            ).exclude(sender=request.user).count()
        })
    
    # Récupérer les groupes de l'utilisateur
    user_groups = Group.objects.filter(
        memberships__user=request.user,
        memberships__is_active=True,
        is_active=True
    ).select_related('created_by').order_by('-last_message_at')[:5]
    
    context = {
        'conversations': conversations_data,
        'groups': user_groups,
    }
    
    return render(request, 'chat/chat_home.html', context)

def chat_list(request):
    return render(request, 'chat_list.html')

def notifications(request):
    if request.user.is_authenticated:
        # Récupérer toutes les notifications
        all_notes = Notification.objects.filter(user=request.user)
        
        # Trier manuellement selon la priorité : non lues récentes > non lues anciennes > lues récentes > lues anciennes
        # Utiliser une clé de tri plus robuste
        def sort_key(notification):
            # Priorité : False (non lue) = 0, True (lue) = 1
            # Puis par date décroissante (plus récent en premier)
            return (notification.is_read, -notification.created_at.timestamp())
        
        notes = sorted(all_notes, key=sort_key)
    else:
        notes = []
    
    # Pour chaque notification de litige, ajouter la première demande d'information en attente
    for note in notes:
        if note.type == 'dispute_message' and note.dispute:
            pending_request = note.dispute.information_requests.filter(
                requested_to=request.user,
                status='pending'
            ).first()
            note.pending_request = pending_request
    
    return render(request, 'notifications.html', {'notifications': notes})

def mark_notification_read(request, notification_id):
    note = get_object_or_404(Notification, id=notification_id, user=request.user)
    note.is_read = True
    note.save()
    return redirect('notifications')

def unread_notifications_count(request):
    """API endpoint pour obtenir le nombre de notifications non lues"""
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

def user_search(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    user_profile = getattr(request.user, 'profile', None)
    user_favorite_games = user_profile.favorite_games if user_profile else []
    
    user_friendships = Friendship.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    )
    
    existing_friends = set()
    for friendship in user_friendships:
        if friendship.user1 == request.user:
            existing_friends.add(friendship.user2.id)
        else:
            existing_friends.add(friendship.user1.id)
    
    existing_requests = set(
        FriendRequest.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user),
            status='pending'
        ).values_list('from_user_id', 'to_user_id')
    )
    
    blocked_users = set()
    for from_id, to_id in existing_requests:
        if from_id == request.user.id:
            blocked_users.add(to_id)
        else:
            blocked_users.add(from_id)
    
    excluded_users = existing_friends | blocked_users | {request.user.id}
    search_query = request.GET.get('q', '').strip()
    
    if search_query:
        # Recherche simple par nom d'utilisateur sans limitation par jeux favoris
        search_results = User.objects.filter(
            username__icontains=search_query
        ).exclude(id__in=excluded_users).select_related('profile')[:50]
        
        recommendations = []
        for user in search_results:
            user_games = user.profile.favorite_games if user.profile else []
            common_games = set(user_favorite_games) & set(user_games) if user_favorite_games else set()
            similarity_score = len(common_games)
            recommendations.append((user, similarity_score, list(common_games)))
    else:
        recommendations = []
        if user_favorite_games:
            potential_users = User.objects.filter(
                profile__favorite_games__overlap=user_favorite_games
            ).exclude(id__in=excluded_users).select_related('profile')[:20]
            
            user_scores = []
            for user in potential_users:
                user_games = user.profile.favorite_games if user.profile else []
                common_games = set(user_favorite_games) & set(user_games)
                similarity_score = len(common_games)
                if similarity_score > 0:
                    user_scores.append((user, similarity_score, list(common_games)))
            
            user_scores.sort(key=lambda x: x[1], reverse=True)
            recommendations = user_scores[:10]
        
        if len(recommendations) < 10:
            remaining_slots = 10 - len(recommendations)
            recommended_user_ids = {user[0].id for user in recommendations}
            
            random_users = User.objects.exclude(
                id__in=excluded_users | recommended_user_ids
            ).select_related('profile').order_by('?')[:remaining_slots]
            
            for user in random_users:
                user_games = user.profile.favorite_games if user.profile else []
                common_games = set(user_favorite_games) & set(user_games) if user_favorite_games else set()
                recommendations.append((user, len(common_games), list(common_games)))
    
    context = {
        'recommendations': recommendations,
        'user_favorite_games': user_favorite_games,
        'search_query': search_query,
    }
    
    return render(request, 'chat/user_search.html', context)

def private_chat(request, user_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    other = get_object_or_404(User, id=user_id)
    
    # Vérifier qu'on ne peut pas chatter avec soi-même
    if other == request.user:
        messages.error(request, "Vous ne pouvez pas chatter avec vous-même.")
        return redirect('chat_home')
    
    # Créer ou récupérer la conversation privée
    conversation = PrivateConversation.objects.filter(
        Q(user1=request.user, user2=other) |
        Q(user1=other, user2=request.user)
    ).first()
    
    if not conversation:
        # Créer une nouvelle conversation
        conversation = PrivateConversation.objects.create(
            user1=request.user,
            user2=other
        )
    
    # Récupérer les messages non lus pour cet utilisateur
    unread_messages = conversation.private_messages.filter(
        is_read=False
    ).exclude(sender=request.user).order_by('created_at')
    
    first_unread_message = unread_messages.first()
    
    # Récupérer les derniers messages (50 max)
    messages_list = conversation.private_messages.select_related('sender').order_by('-created_at')[:50]
    messages_list = list(reversed(messages_list))  # Ordre chronologique
    
    # Marquer les messages comme lus
    for message in unread_messages:
        message.is_read = True
        message.read_at = timezone.now()
    
    PrivateMessage.objects.bulk_update(unread_messages, ['is_read', 'read_at'])
    
    # Récupérer le profil de l'autre utilisateur
    try:
        other_profile = Profile.objects.get(user=other)
    except Profile.DoesNotExist:
        other_profile = None
    
    context = {
        'other_user': other,
        'other_user_profile': other_profile,
        'conversation': conversation,
        'messages': messages_list,
        'first_unread_message': first_unread_message,
    }
    
    return render(request, 'chat/private_chat.html', context)

@require_POST
def send_private_message(request, conversation_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Non authentifié'})
    
    try:
        conversation = PrivateConversation.objects.get(id=conversation_id)
        
        # Vérifier que l'utilisateur fait partie de cette conversation
        if request.user not in [conversation.user1, conversation.user2]:
            return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
        
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        file = request.FILES.get('file')
        reply_to_id = request.POST.get('reply_to')
        
        # Vérifier qu'il y a au moins du contenu ou un fichier
        if not content and not image and not file:
            return JsonResponse({'success': False, 'error': 'Message vide'})
        
        # Vérifier la réponse si spécifiée
        reply_to = None
        if reply_to_id:
            try:
                reply_to = PrivateMessage.objects.get(id=reply_to_id, conversation=conversation)
            except PrivateMessage.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Message de réponse introuvable'})
        
        # Créer le message
        message = PrivateMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            image=image,
            file=file,
            reply_to=reply_to
        )
        
        # Marquer la conversation comme mise à jour
        conversation.last_message = message
        conversation.updated_at = message.created_at
        conversation.save()
        
        # Diffuser le message via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        room_group_name = f'private_chat_{conversation_id}'
        
        message_data = {
            'id': str(message.id),
            'content': message.content,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'created_at': message.created_at.isoformat(),
            'is_own': message.sender == request.user,
            'image': message.image.url if message.image else None,
            'file': message.file.url if message.file else None,
            'file_name': message.file.name.split('/')[-1] if message.file else None,
            'reply_to': {
                'id': str(reply_to.id),
                'content': reply_to.content[:50] + '...' if len(reply_to.content) > 50 else reply_to.content,
                'sender': reply_to.sender.username
            } if reply_to else None
        }
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': message_data
        })
        
    except PrivateConversation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversation introuvable'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_private_messages(request, conversation_id):
    try:
        conversation = get_object_or_404(PrivateConversation, id=conversation_id)
        
        # Vérifier que l'utilisateur fait partie de la conversation
        if request.user not in [conversation.user1, conversation.user2]:
            return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
        
        # Paramètres de pagination
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 20)), 50)  # Max 50 messages
        offset = (page - 1) * limit
        
        # Récupérer les messages
        messages_query = conversation.private_messages.select_related('sender').order_by('-created_at')
        total_messages = messages_query.count()
        messages_list = messages_query[offset:offset + limit]
        
        messages_data = []
        for message in reversed(messages_list):  # Ordre chronologique
            message_data = {
                'id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read,
                'is_own': message.sender == request.user,
                'is_edited': message.is_edited,
                'image': message.image.url if message.image else None,
                'file': message.file.url if message.file else None,
                'file_name': message.file.name.split('/')[-1] if message.file else None,
            }
            
            # Ajouter les données de réponse si applicable
            if message.reply_to:
                message_data['reply_to'] = {
                    'id': str(message.reply_to.id),
                    'content': message.reply_to.content[:50] + '...' if len(message.reply_to.content) > 50 else message.reply_to.content,
                    'sender': message.reply_to.sender.username
                }
            else:
                message_data['reply_to'] = None
                
            messages_data.append(message_data)
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_messages,
                'has_more': offset + limit < total_messages
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération messages: {e}")
        return JsonResponse({'success': False, 'error': 'Erreur serveur'})

def group_list(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Récupérer les groupes dont l'utilisateur est membre
    user_groups = Group.objects.filter(
        memberships__user=request.user,
        memberships__is_active=True,
        is_active=True
    ).select_related('created_by').prefetch_related('memberships').order_by('-last_message_at')
    
    # Ajouter des informations supplémentaires pour chaque groupe
    groups_data = []
    for group in user_groups:
        membership = group.memberships.filter(user=request.user, is_active=True).first()
        last_message = group.group_messages.order_by('-created_at').first()
        
        groups_data.append({
            'group': group,
            'is_admin': membership.is_admin if membership else False,
            'members_count': group.memberships.filter(is_active=True).count(),
            'last_message': last_message,
            'unread_count': 0  # TODO: Implémenter le comptage des messages non lus
        })
    
    context = {
        'groups_data': groups_data,
    }
    
    return render(request, 'chat/group_list.html', context)

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, "Le nom du groupe est requis.")
            return render(request, 'chat/create_group.html')
        
        if len(name) > 100:
            messages.error(request, "Le nom du groupe est trop long (max 100 caractères).")
            return render(request, 'chat/create_group.html')
        
        try:
            # Créer le groupe
            group = Group.objects.create(
                name=name,
                description=description,
                created_by=request.user
            )
            
            # Ajouter le créateur comme membre admin
            GroupMembership.objects.create(
                user=request.user,
                group=group,
                is_admin=True,
                added_by=request.user
            )
            
            messages.success(request, f"Groupe '{name}' créé avec succès.")
            return redirect('group_chat', group_id=group.id)
            
        except Exception as e:
            logger.error(f"Erreur création groupe: {e}")
            messages.error(request, "Erreur lors de la création du groupe.")
    
    return render(request, 'chat/create_group.html')

def group_chat(request, group_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        group = get_object_or_404(Group, id=group_id, is_active=True)
        
        # Vérifier que l'utilisateur est membre du groupe
        membership = GroupMembership.objects.filter(
            user=request.user,
            group=group,
            is_active=True
        ).first()
        
        if not membership:
            messages.error(request, "Vous n'êtes pas membre de ce groupe.")
            return redirect('group_list')
        
        # Récupérer les messages non lus pour cet utilisateur
        unread_messages = GroupMessage.objects.filter(
            group=group
        ).exclude(
            read_by__user=request.user
        ).exclude(
            sender=request.user
        ).order_by('created_at')
        
        first_unread_message = unread_messages.first()
        
        # Récupérer les derniers messages (50 max)
        messages_list = group.group_messages.select_related('sender').order_by('-created_at')[:50]
        messages_list = list(reversed(messages_list))  # Ordre chronologique
        
        # Marquer les messages comme lus
        for message in messages_list:
            if message.sender != request.user:
                GroupMessageRead.objects.get_or_create(
                    message=message,
                    user=request.user
                )
        
        # Récupérer les membres du groupe
        members = GroupMembership.objects.filter(
            group=group,
            is_active=True
        ).select_related('user').order_by('-is_admin', 'joined_at')
        
        context = {
            'group': group,
            'membership': membership,
            'messages': messages_list,
            'members': members,
            'member_count': members.count(),
            'first_unread_message': first_unread_message,
        }
        
        return render(request, 'chat/group_chat.html', context)
        
    except Exception as e:
        logger.error(f"Erreur accès groupe: {e}")
        messages.error(request, "Erreur lors de l'accès au groupe.")
        return redirect('group_list')

@require_POST
def send_group_message(request, group_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Non authentifié'})
    
    try:
        group = Group.objects.get(id=group_id)
        
        # Vérifier que l'utilisateur est membre du groupe
        if not group.members.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
        
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        file = request.FILES.get('file')
        reply_to_id = request.POST.get('reply_to')
        
        # Vérifier qu'il y a au moins du contenu ou un fichier
        if not content and not image and not file:
            return JsonResponse({'success': False, 'error': 'Message vide'})
        
        # Vérifier la réponse si spécifiée
        reply_to = None
        if reply_to_id:
            try:
                reply_to = GroupMessage.objects.get(id=reply_to_id, group=group)
            except GroupMessage.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Message de réponse introuvable'})
        
        # Créer le message
        message = GroupMessage.objects.create(
            group=group,
            sender=request.user,
            content=content,
            image=image,
            file=file,
            reply_to=reply_to
        )
        
        # Diffuser le message via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        room_group_name = f'group_chat_{group_id}'
        
        message_data = {
            'id': str(message.id),
            'content': message.content,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'created_at': message.created_at.isoformat(),
            'is_own': message.sender == request.user,
            'image': message.image.url if message.image else None,
            'file': message.file.url if message.file else None,
            'file_name': message.file.name.split('/')[-1] if message.file else None,
            'reply_to': {
                'id': str(reply_to.id),
                'content': reply_to.content[:50] + '...' if len(reply_to.content) > 50 else reply_to.content,
                'sender': reply_to.sender.username
            } if reply_to else None
        }
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': message_data
        })
        
    except Group.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Groupe introuvable'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_group_messages(request, group_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Non authentifié'})
    
    try:
        group = get_object_or_404(Group, id=group_id, is_active=True)
        
        # Vérifier que l'utilisateur est membre du groupe
        membership = GroupMembership.objects.filter(
            user=request.user,
            group=group,
            is_active=True
        ).first()
        
        if not membership:
            return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
        
        # Paramètres de pagination
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 20)), 50)  # Max 50 messages
        offset = (page - 1) * limit
        
        # Récupérer les messages
        messages_query = group.group_messages.select_related('sender').order_by('-created_at')
        total_messages = messages_query.count()
        messages_list = messages_query[offset:offset + limit]
        
        messages_data = []
        for message in reversed(messages_list):  # Ordre chronologique
            messages_data.append({
                'id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'created_at': message.created_at.isoformat(),
                'is_own': message.sender == request.user,
                'is_edited': message.is_edited,
                'image': message.image.url if message.image else None,
                'file': message.file.url if message.file else None,
                'file_name': message.file.name.split('/')[-1] if message.file else None,
                'reply_to': {
                    'id': str(message.reply_to.id),
                    'content': message.reply_to.content[:50] + '...' if len(message.reply_to.content) > 50 else message.reply_to.content,
                    'sender': message.reply_to.sender.username
                } if message.reply_to else None
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_messages,
                'has_more': offset + limit < total_messages
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération messages groupe: {e}")
        return JsonResponse({'success': False, 'error': 'Erreur serveur'})

def group_members(request, group_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        group = get_object_or_404(Group, id=group_id, is_active=True)
        
        # Vérifier que l'utilisateur est membre du groupe
        user_membership = GroupMembership.objects.filter(
            user=request.user,
            group=group,
            is_active=True
        ).first()
        
        if not user_membership:
            messages.error(request, "Vous n'êtes pas membre de ce groupe.")
            return redirect('group_list')
        
        # Récupérer tous les membres
        members = GroupMembership.objects.filter(
            group=group,
            is_active=True
        ).select_related('user', 'added_by').order_by('-is_admin', 'joined_at')
        
        context = {
            'group': group,
            'members': members,
            'user_membership': user_membership,
            'can_manage': user_membership.is_admin or group.created_by == request.user,
        }
        
        return render(request, 'chat/group_members.html', context)
        
    except Exception as e:
        logger.error(f"Erreur accès membres groupe: {e}")
        messages.error(request, "Erreur lors de l'accès aux membres du groupe.")
        return redirect('group_list')

def group_settings(request, group_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        group = get_object_or_404(Group, id=group_id, is_active=True)
        
        # Vérifier que l'utilisateur est membre du groupe
        user_membership = GroupMembership.objects.filter(
            user=request.user,
            group=group,
            is_active=True
        ).first()
        
        if not user_membership:
            messages.error(request, "Vous n'êtes pas membre de ce groupe.")
            return redirect('group_list')
        
        context = {
            'group': group,
            'membership': user_membership,
            'is_admin': user_membership.is_admin,
        }
        
        return render(request, 'chat/group_settings.html', context)
        
    except Exception as e:
        logger.error(f"Erreur accès paramètres groupe: {e}")
        messages.error(request, "Erreur lors de l'accès aux paramètres du groupe.")
        return redirect('group_list')

def add_group_member(request, group_id):
    return JsonResponse({'success': True})

def remove_group_member(request, group_id):
    return JsonResponse({'success': True})

def promote_member(request, group_id):
    return JsonResponse({'success': True})

def leave_group(request, group_id):
    return JsonResponse({'success': True})

def friend_requests(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Récupérer les demandes d'ami reçues (en attente)
    pending_received = FriendRequest.objects.filter(
        to_user=request.user, 
        status='pending'
    ).select_related('from_user')
    
    # Récupérer les demandes d'ami envoyées (en attente)
    pending_sent = FriendRequest.objects.filter(
        from_user=request.user, 
        status='pending'
    ).select_related('to_user')
    
    # Récupérer les amis existants (friendships bidirectionnelles)
    user_friendships = Friendship.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    )
    
    friends = []
    for friendship in user_friendships:
        if friendship.user1 == request.user:
            friends.append(friendship.user2)
        else:
            friends.append(friendship.user1)
    
    context = {
        'friends': friends,
        'pending_received': pending_received,
        'pending_sent': pending_sent,
    }
    
    return render(request, 'chat/friends.html', context)

def send_friend_request(request, user_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        to_user = User.objects.get(id=user_id)
        
        # Vérifier qu'on n'envoie pas une demande à soi-même
        if to_user == request.user:
            messages.error(request, "Vous ne pouvez pas vous envoyer une demande d'ami.")
            return redirect('user_search')
        
        # Vérifier si une demande existe déjà
        existing_request = FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=request.user),
            status='pending'
        ).first()
        
        if existing_request:
            messages.warning(request, "Une demande d'ami est déjà en cours avec cet utilisateur.")
            return redirect('user_search')
        
        # Vérifier si ils sont déjà amis
        existing_friendship = Friendship.objects.filter(
            Q(user1=request.user, user2=to_user) |
            Q(user1=to_user, user2=request.user)
        ).first()
        
        if existing_friendship:
            messages.info(request, "Vous êtes déjà amis avec cet utilisateur.")
            return redirect('user_search')
        
        # Créer la demande d'ami
        FriendRequest.objects.create(
            from_user=request.user,
            to_user=to_user,
            status='pending'
        )
        
        messages.success(request, f"Demande d'ami envoyée à {to_user.username}.")
        
    except User.DoesNotExist:
        messages.error(request, "Utilisateur introuvable.")
    
    return redirect('user_search')

def accept_friend_request(request, request_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            to_user=request.user,
            status='pending'
        )
        
        # Marquer la demande comme acceptée
        friend_request.status = 'accepted'
        friend_request.responded_at = timezone.now()
        friend_request.save()
        
        # Créer l'amitié bidirectionnelle
        Friendship.objects.create(
            user1=friend_request.from_user,
            user2=friend_request.to_user
        )
        
        messages.success(request, f"Vous êtes maintenant ami avec {friend_request.from_user.username}.")
        
    except FriendRequest.DoesNotExist:
        messages.error(request, "Demande d'ami introuvable.")
    
    return redirect('friend_requests')

def decline_friend_request(request, request_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            to_user=request.user,
            status='pending'
        )
        
        # Marquer la demande comme refusée
        friend_request.status = 'declined'
        friend_request.responded_at = timezone.now()
        friend_request.save()
        
        messages.info(request, f"Demande d'ami de {friend_request.from_user.username} refusée.")
        
    except FriendRequest.DoesNotExist:
        messages.error(request, "Demande d'ami introuvable.")
    
    return redirect('friend_requests')

def cancel_friend_request(request, request_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            from_user=request.user,
            status='pending'
        )
        
        # Marquer la demande comme annulée
        friend_request.status = 'cancelled'
        friend_request.responded_at = timezone.now()
        friend_request.save()
        
        messages.info(request, f"Demande d'ami à {friend_request.to_user.username} annulée.")
        
    except FriendRequest.DoesNotExist:
        messages.error(request, "Demande d'ami introuvable.")
    
    return redirect('friend_requests')

# ===== Boutique E-commerce =====

def shop_home(request):
    try:
        categories = ProductCategory.objects.filter(is_active=True, parent=None)[:6]
        featured_products = Product.objects.filter(status='active', is_featured=True)[:8]
        new_products = Product.objects.filter(status='active').order_by('-created_at')[:8]
        context = {
            'categories': categories,
            'featured_products': featured_products,
            'new_products': new_products,
        }
        return render(request, 'shop/home.html', context)
    except Exception as e:
        logger.error(f"Erreur dans shop_home: {e}")
        messages.error(request, "Erreur lors du chargement de la boutique")
        return redirect('index')

def shop_products(request):
    try:
        products = Product.objects.filter(status='active')
        categories = ProductCategory.objects.filter(is_active=True)
        category_slug = request.GET.get('category')
        if category_slug:
            products = products.filter(category__slug=category_slug)
        min_price = request.GET.get('min_price')
        if min_price:
            products = products.filter(price__gte=min_price)
        max_price = request.GET.get('max_price')
        if max_price:
            products = products.filter(price__lte=max_price)
        sort = request.GET.get('sort', '-created_at')
        if sort in ['name', '-name', 'price', '-price', '-created_at', 'created_at']:
            products = products.order_by(sort)
        paginator = Paginator(products, 12)
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)
        context = {
            'products': products,
            'categories': categories,
            'current_sort': sort,
            'page_title': 'Boutique Gaming - Blizz',
        }
        return render(request, 'shop/products.html', context)
    except Exception as e:
        logger.error(f"Erreur dans shop_products: {e}")
        messages.error(request, "Erreur lors du chargement des produits")
        return redirect('shop_products')

def shop_product_detail(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug, status='active')
        # Récupérer toutes les images du produit pour le carrousel
        product_images = product.images.all().order_by('order')
        # Si pas d'images, utiliser l'image principale
        if not product_images.exists() and product.featured_image:
            product_images = [product.featured_image]
        related_products = Product.objects.filter(category=product.category, status='active').exclude(id=product.id)[:4]
        context = {
            'product': product,
            'product_images': product_images,
            'related_products': related_products,
        }
        return render(request, 'shop/product_detail.html', context)
    except Exception as e:
        logger.error(f"Erreur dans shop_product_detail: {e}")
        messages.error(request, "Produit non trouvé")
        return redirect('shop_products')


# ===== Panier =====

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

@require_POST
def add_to_cart(request):
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Produit non spécifié'})
        
        product = get_object_or_404(Product, id=product_id, status='active')
        price = product.price
        
        cart = get_or_create_cart(request)
        
        # Créer ou mettre à jour l'item du panier (système simplifié)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=None,  # Pas de variantes
            defaults={'quantity': quantity, 'price': price}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Produit ajouté au panier', 
            'cart_count': cart.get_total_items()
        })
        
    except Exception as e:
        logger.error(f"Erreur add_to_cart: {e}")
        return JsonResponse({'success': False, 'message': "Erreur lors de l'ajout au panier"})

def cart_view(request):
    try:
        cart = get_or_create_cart(request)
        return render(request, 'shop/cart.html', {'cart': cart})
    except Exception as e:
        logger.error(f"Erreur cart_view: {e}")
        messages.error(request, "Erreur lors du chargement du panier")
        return redirect('shop_products')

@require_POST
def update_cart_item(request):
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        logger.info(f"[UPDATE_CART_ITEM] Requête reçue - item_id: {item_id}, quantity: {quantity}")
        
        cart = get_or_create_cart(request)
        logger.info(f"[UPDATE_CART_ITEM] Panier récupéré: {cart.id}")
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        logger.info(f"[UPDATE_CART_ITEM] Item trouvé: {cart_item.product.name}, quantité actuelle: {cart_item.quantity}")
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            logger.info(f"[UPDATE_CART_ITEM] Quantité mise à jour: {quantity}")
            
            # Convertir les prix dans la devise de l'utilisateur
            from .currency_service import CurrencyService
            user_currency = 'EUR'  # Devise de base (prix stockés en EUR)
            if hasattr(request.user, 'currency_preference') and request.user.currency_preference.preferred_currency:
                user_currency = request.user.currency_preference.preferred_currency
            
            # Convertir les prix si nécessaire
            item_total_eur = float(cart_item.get_total_price())
            cart_total_eur = float(cart.get_total_price())
            
            if user_currency != 'EUR':
                item_total_converted = CurrencyService.convert_amount(item_total_eur, 'EUR', user_currency)
                cart_total_converted = CurrencyService.convert_amount(cart_total_eur, 'EUR', user_currency)
            else:
                item_total_converted = item_total_eur
                cart_total_converted = cart_total_eur
            
            # Retourner les données mises à jour pour le calcul en temps réel
            response_data = {
                'success': True,
                'item_total_price': item_total_converted,
                'cart_total_price': cart_total_converted,
                'cart_count': cart.get_total_items(),
                'currency': user_currency
            }
            logger.info(f"[UPDATE_CART_ITEM] Réponse: {response_data}")
            return JsonResponse(response_data)
        else:
            cart_item.delete()
            logger.info(f"[UPDATE_CART_ITEM] Item supprimé")
            return JsonResponse({
                'success': True,
                'item_deleted': True,
                'cart_total_price': float(cart.get_total_price()),
                'cart_count': cart.get_total_items()
            })
    except Exception as e:
        logger.error(f"Erreur update_cart_item: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'message': 'Erreur lors de la mise à jour'})

@require_POST
def remove_from_cart(request):
    try:
        item_id = request.POST.get('item_id')
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
        # Convertir les prix dans la devise de l'utilisateur
        from .currency_service import CurrencyService
        user_currency = 'EUR'  # Devise de base (prix stockés en EUR)
        if hasattr(request.user, 'currency_preference') and request.user.currency_preference.preferred_currency:
            user_currency = request.user.currency_preference.preferred_currency
        
        cart_total_eur = float(cart.get_total_price())
        
        if user_currency != 'EUR':
            cart_total_converted = CurrencyService.convert_amount(cart_total_eur, 'EUR', user_currency)
        else:
            cart_total_converted = cart_total_eur
        
        return JsonResponse({
            'success': True,
            'item_deleted': True,
            'cart_total_price': cart_total_converted,
            'cart_count': cart.get_total_items(),
            'currency': user_currency
        })
    except Exception as e:
        logger.error(f"Erreur remove_from_cart: {e}")
        return JsonResponse({'success': False, 'message': 'Erreur lors de la suppression'})

# ===== Checkout et Paiement Boutique (CinetPay) =====

def checkout(request):
    try:
        cart = get_or_create_cart(request)
        if cart.is_empty:
            messages.warning(request, 'Votre panier est vide')
            return redirect('cart_view')
        if request.method == 'POST':
            try:
                # Vérifier le montant total avant de créer la commande
                total_amount = cart.get_total_price()
                
                # Convertir vers XOF pour vérifier les limites CinetPay
                from blizzgame.cinetpay_utils import validate_cinetpay_amount
                converted_amount = CurrencyService.convert_amount(total_amount, 'EUR', 'XOF')
                is_valid, message = validate_cinetpay_amount(converted_amount, 'XOF')
                
                if not is_valid:
                    logger.warning(f"Commande refusée - montant trop élevé: {total_amount} EUR → {converted_amount} XOF")
                    messages.error(request, f"Le montant de votre commande est trop élevé pour le paiement. {message}")
                    return render(request, 'shop/checkout.html', {'cart': cart})
                
                # Combiner le code pays et le numéro de téléphone
                phone_country_code = request.POST.get('phone_country_code', '')
                phone_number = request.POST.get('phone', '')
                full_phone = phone_country_code + phone_number if phone_country_code and phone_number else request.POST.get('phone', '')
                
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    customer_email=request.POST.get('email'),
                    customer_phone=full_phone,
                    customer_first_name=request.POST.get('first_name'),
                    customer_last_name=request.POST.get('last_name'),
                    shipping_address_line1=request.POST.get('address_line1'),
                    shipping_address_line2=request.POST.get('address_line2', ''),
                    shipping_city=request.POST.get('city'),
                    shipping_state=request.POST.get('state'),
                    shipping_postal_code=request.POST.get('postal_code'),
                    shipping_country=request.POST.get('country'),
                    subtotal=cart.get_total_price(),
                    total_amount=cart.get_total_price(),
                )
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        variant=cart_item.variant,
                        product_name=cart_item.product.name,
                        product_price=cart_item.get_current_price(),  # Prix actuel
                        quantity=cart_item.quantity,
                        total_price=cart_item.get_total_price()
                    )
                cart.items.all().delete()
                return redirect('shop_payment', order_id=order.id)
            except Exception as e:
                logger.error(f"Erreur lors de la création de commande: {e}")
                messages.error(request, 'Erreur lors de la création de la commande')
        return render(request, 'shop/checkout.html', {'cart': cart})
    except Exception as e:
        logger.error(f"Erreur checkout: {e}")
        messages.error(request, 'Erreur lors du processus de commande')
        return redirect('cart_view')

def shop_payment(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        if order.user and request.user.is_authenticated and order.user != request.user:
            error_msg = 'Commande non autorisée'
            
            # Si c'est une requête AJAX, retourner JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            
            messages.error(request, error_msg)
            return redirect('shop_products')
        if request.method == 'POST':
            logger.info(f"[SHOP PAYMENT] Requête POST reçue pour commande {order_id}")
            logger.info(f"[SHOP PAYMENT] Données POST: {request.POST}")
            
            # Combiner le code pays et le numéro de téléphone
            phone_country_code = request.POST.get('customer_phone_country_code', '')
            phone_number = request.POST.get('customer_phone_number', '')
            full_phone = phone_country_code + phone_number if phone_country_code and phone_number else request.POST.get('customer_phone_number', '')
            
            customer_data = {
                'customer_name': request.POST.get('customer_name'),
                'customer_surname': request.POST.get('customer_surname'),
                'customer_email': request.POST.get('customer_email'),
                'customer_phone_number': full_phone,
                'customer_address': request.POST.get('customer_address'),
                'customer_city': request.POST.get('customer_city'),
                'customer_country': request.POST.get('customer_country'),
                'customer_state': request.POST.get('customer_state'),
                'customer_zip_code': request.POST.get('customer_zip_code'),
            }
            
            # Rediriger les pays non-africains vers le Sénégal pour CinetPay
            african_countries = ['CI', 'SN', 'BF', 'ML', 'NE', 'TG', 'BJ', 'GN', 'CM', 'CD', 'CDUSD']
            if customer_data['customer_country'] and customer_data['customer_country'] not in african_countries:
                # Pays non-africain - utiliser le Sénégal pour CinetPay
                logger.info(f"Pays {customer_data['customer_country']} redirigé vers le Sénégal pour CinetPay (shop)")
                customer_data['customer_country'] = 'SN'  # Sénégal
            
            logger.info(f"[SHOP PAYMENT] Données client: {customer_data}")
            
            # Convertir le montant vers XOF pour CinetPay
            # Les produits sont stockés en EUR, donc on convertit depuis EUR vers XOF
            from blizzgame.cinetpay_utils import validate_cinetpay_amount
            
            # Log pour débogage
            logger.info(f"[SHOP PAYMENT] Montant original: {order.total_amount} EUR")
            
            converted_amount = CurrencyService.convert_amount(
                order.total_amount, 'EUR', 'XOF'
            )
            
            logger.info(f"[SHOP PAYMENT] Montant converti: {converted_amount} XOF")
            
            # Valider le montant converti
            is_valid, message = validate_cinetpay_amount(converted_amount, 'XOF')
            if not is_valid:
                logger.error(f"[SHOP PAYMENT] Validation échouée: {message}")
                error_msg = f"Montant invalide: {message}"
                
                # Si c'est une requête AJAX, retourner JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                
                messages.error(request, error_msg)
                return render(request, 'shop/checkout.html', {
                    'order': order,
                    'error': error_msg
                })
            
            # Mettre à jour la commande avec le montant converti pour CinetPay
            order.total_amount = converted_amount
            order.subtotal = converted_amount
            
            # Utiliser l'API CinetPay réelle pour le dropshipping
            cinetpay_api = CinetPayAPI()
            result = cinetpay_api.initiate_payment(order, customer_data)
            if result['success']:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    logger.info(f"URL de redirection CinetPay: {result['payment_url']}")
                    return JsonResponse({'success': True, 'redirect_url': result['payment_url']})
                return redirect(result['payment_url'])
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': result['error']})
                messages.error(request, f"Erreur de paiement: {result['error']}")
        
        # Ajouter la devise de l'utilisateur au contexte
        user_currency = CurrencyService.get_user_currency(request.user)
        return render(request, 'shop/payment.html', {
            'order': order, 
            'user_profile': getattr(request.user, 'profile', None) if request.user.is_authenticated else None,
            'user_currency': user_currency
        })
    except Exception as e:
        logger.error(f"Erreur shop_payment: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Si c'est une requête AJAX, retourner JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'error': f'Erreur lors du processus de paiement: {str(e)}'
            })
        
        messages.error(request, 'Erreur lors du processus de paiement')
        return redirect('shop_products')

@csrf_exempt
def shop_cinetpay_notification(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                notification_data = json.loads(request.body)
            else:
                notification_data = request.POST.dict()
            logger.info(f"Notification CinetPay reçue: {notification_data}")
            success = handle_cinetpay_notification(notification_data)
            if success:
                return HttpResponse('OK', status=200)
            return HttpResponse('Error', status=400)
        except Exception as e:
            logger.error(f"Erreur dans shop_cinetpay_notification: {e}")
            return HttpResponse('Error', status=500)
    return HttpResponse('Method not allowed', status=405)

@csrf_exempt
def shop_payment_success(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        logger.info(f"[SHOP PAYMENT SUCCESS] Commande {order.order_number} - Statut actuel: {order.payment_status}")
        
        # Vérifier si la transaction CinetPay existe
        if hasattr(order, 'cinetpay_transaction'):
            cinetpay_transaction = order.cinetpay_transaction
            logger.info(f"[SHOP PAYMENT SUCCESS] Transaction CinetPay: {cinetpay_transaction.cinetpay_transaction_id} - Statut: {cinetpay_transaction.status}")
            
            # Si la transaction n'est pas encore marquée comme complétée, essayer de la vérifier
            if cinetpay_transaction.status != 'completed':
                logger.info(f"[SHOP PAYMENT SUCCESS] Vérification du statut de paiement CinetPay...")
                from blizzgame.cinetpay_utils import CinetPayAPI
                
                cinetpay_api = CinetPayAPI()
                verification_result = cinetpay_api.verify_payment(cinetpay_transaction.cinetpay_transaction_id)
                
                if verification_result and verification_result.get('data', {}).get('payment_status') == 'ACCEPTED':
                    logger.info(f"[SHOP PAYMENT SUCCESS] Paiement confirmé par CinetPay")
                    cinetpay_transaction.status = 'completed'
                    cinetpay_transaction.completed_at = timezone.now()
                    cinetpay_transaction.save()
                    
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.save()
                    
                    # Shopify désactivé - Pas nécessaire pour le moment
                    # from .shopify_utils import create_shopify_order_from_blizz_order, mark_order_as_paid_in_shopify
                    # try:
                    #     shopify_order = create_shopify_order_from_blizz_order(order)
                    #     if shopify_order:
                    #         mark_order_as_paid_in_shopify(order)
                    #         logger.info(f"Commande transférée vers Shopify: {order.order_number}")
                    #     else:
                    #         logger.error(f"Échec de création commande Shopify pour: {order.order_number}")
                    # except Exception as e:
                    #     logger.error(f"Erreur lors du transfert Shopify: {e}")
                else:
                    logger.warning(f"[SHOP PAYMENT SUCCESS] Paiement non confirmé par CinetPay: {verification_result}")
            else:
                # Transaction déjà marquée comme complétée
                order.payment_status = 'paid'
                order.status = 'processing'
                order.save()
        else:
            logger.warning(f"[SHOP PAYMENT SUCCESS] Aucune transaction CinetPay trouvée pour la commande {order.order_number}")
            # Marquer comme payé même sans transaction CinetPay (cas de test ou autre méthode de paiement)
            order.payment_status = 'paid'
            order.status = 'processing'
            order.save()
        
        logger.info(f"[SHOP PAYMENT SUCCESS] Commande {order.order_number} - Nouveau statut: {order.payment_status}")
        
        # Créer une notification pour l'utilisateur
        if order.user:
            Notification.objects.create(
                user=order.user,
                type='transaction_update',
                title='Commande confirmée',
                content=f"Votre commande #{order.order_number} a été confirmée et est en cours de traitement. Vous recevrez un email de confirmation sous peu.",
                order=order
            )
        
        # Message de succès et redirection vers la page des commandes
        messages.success(request, f'🎉 Commande confirmée avec succès! Votre commande #{order.order_number} est en cours de traitement.')
        return redirect('my_orders')
        
    except Exception as e:
        logger.error(f"Erreur shop_payment_success: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, 'Erreur lors de la confirmation de paiement')
        return redirect('shop_products')

@csrf_exempt
def shop_payment_failed(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        return render(request, 'shop/payment_failed.html', {'order': order})
    except Exception as e:
        logger.error(f"Erreur shop_payment_failed: {e}")
        messages.error(request, "Erreur lors de l'affichage de l'échec")
        return redirect('shop_products')

@login_required
def my_orders(request):
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        orders = paginator.get_page(page_number)
        return render(request, 'shop/my_orders.html', {'orders': orders})
    except Exception as e:
        logger.error(f"Erreur my_orders: {e}")
        messages.error(request, 'Erreur lors du chargement des commandes')
        return redirect('shop_products')

@login_required
def order_detail(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        return render(request, 'shop/order_detail.html', {'order': order})
    except Exception as e:
        logger.error(f"Erreur order_detail: {e}")
        messages.error(request, 'Commande non trouvée')
        return redirect('my_orders')

@login_required
def sync_shopify_products(request):
    """Fonction désactivée - Shopify pas nécessaire pour le moment"""
    messages.info(request, 'Synchronisation Shopify désactivée')
    return redirect('index')

# ===== Paramétrage des infos de paiement vendeur (stubs) =====

@login_required
def seller_payment_setup(request):
    payment_info, _ = SellerPaymentInfo.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        payment_info.preferred_payment_method = request.POST.get('preferred_payment_method', payment_info.preferred_payment_method)
        payment_info.phone_number = request.POST.get('phone_number', payment_info.phone_number)
        payment_info.operator = request.POST.get('operator', payment_info.operator)
        payment_info.country = request.POST.get('country', payment_info.country)
        payment_info.bank_name = request.POST.get('bank_name', payment_info.bank_name)
        payment_info.account_number = request.POST.get('account_number', payment_info.account_number)
        payment_info.account_holder_name = request.POST.get('account_holder_name', payment_info.account_holder_name)
        payment_info.card_number = request.POST.get('card_number', payment_info.card_number)
        payment_info.card_holder_name = request.POST.get('card_holder_name', payment_info.card_holder_name)
        
        # Vérifier les informations de paiement
        try:
            from blizzgame.payment_verification import PaymentVerificationService
            
            is_valid, errors = PaymentVerificationService.verify_payment_info(payment_info)
            
            if is_valid:
                # Marquer comme vérifié
                payment_info.is_verified = True
                payment_info.verified_at = timezone.now()
                payment_info.verification_failed_reason = None
                payment_info.save()
                
                messages.success(request, 'Informations de paiement vérifiées et mises à jour. Vous pouvez maintenant créer des annonces!')
                return redirect('create')
            else:
                # Marquer comme non vérifié et sauvegarder les erreurs
                payment_info.is_verified = False
                payment_info.verification_attempts += 1
                payment_info.last_verification_attempt = timezone.now()
                payment_info.verification_failed_reason = '; '.join(errors)
                payment_info.save()
                
                # Afficher les erreurs
                for error in errors:
                    messages.error(request, f'❌ {error}')
                
                messages.warning(request, 'Veuillez corriger les erreurs ci-dessus avant de pouvoir créer des annonces.')
        except Exception as e:
            # En cas d'erreur, marquer comme non vérifié
            payment_info.is_verified = False
            payment_info.verification_failed_reason = f'Erreur de vérification: {str(e)}'
            payment_info.save()
            
            messages.error(request, f'Erreur lors de la vérification: {str(e)}')
            messages.warning(request, 'Veuillez réessayer ou contacter le support.')
    
    # Préparer le contexte pour le template
    context = {
        'payment_info': payment_info,
        'countries': [
            # Afrique de l'Ouest
            ('CI', 'Côte d\'Ivoire'),
            ('SN', 'Sénégal'),
            ('BF', 'Burkina Faso'),
            ('ML', 'Mali'),
            ('NE', 'Niger'),
            ('TG', 'Togo'),
            ('BJ', 'Bénin'),
            ('GN', 'Guinée'),
            ('LR', 'Libéria'),
            ('SL', 'Sierra Leone'),
            ('GH', 'Ghana'),
            ('NG', 'Nigeria'),
            
            # Afrique Centrale
            ('CM', 'Cameroun'),
            ('TD', 'Tchad'),
            ('CF', 'République centrafricaine'),
            ('CD', 'République démocratique du Congo'),
            ('CG', 'République du Congo'),
            ('GA', 'Gabon'),
            ('GQ', 'Guinée équatoriale'),
            ('ST', 'São Tomé-et-Príncipe'),
            
            # Afrique de l'Est
            ('KE', 'Kenya'),
            ('UG', 'Ouganda'),
            ('TZ', 'Tanzanie'),
            ('RW', 'Rwanda'),
            ('BI', 'Burundi'),
            ('ET', 'Éthiopie'),
            ('ER', 'Érythrée'),
            ('DJ', 'Djibouti'),
            ('SO', 'Somalie'),
            ('SS', 'Soudan du Sud'),
            ('SD', 'Soudan'),
            
            # Afrique Australe
            ('ZA', 'Afrique du Sud'),
            ('BW', 'Botswana'),
            ('NA', 'Namibie'),
            ('ZW', 'Zimbabwe'),
            ('ZM', 'Zambie'),
            ('MW', 'Malawi'),
            ('MZ', 'Mozambique'),
            ('MG', 'Madagascar'),
            ('MU', 'Maurice'),
            ('SC', 'Seychelles'),
            ('KM', 'Comores'),
            ('LS', 'Lesotho'),
            ('SZ', 'Eswatini'),
            
            # Europe
            ('FR', 'France'),
            ('DE', 'Allemagne'),
            ('IT', 'Italie'),
            ('ES', 'Espagne'),
            ('GB', 'Royaume-Uni'),
            ('NL', 'Pays-Bas'),
            ('BE', 'Belgique'),
            ('CH', 'Suisse'),
            ('AT', 'Autriche'),
            ('PT', 'Portugal'),
            ('IE', 'Irlande'),
            ('DK', 'Danemark'),
            ('SE', 'Suède'),
            ('NO', 'Norvège'),
            ('FI', 'Finlande'),
            ('PL', 'Pologne'),
            ('CZ', 'République tchèque'),
            ('HU', 'Hongrie'),
            ('RO', 'Roumanie'),
            ('BG', 'Bulgarie'),
            ('HR', 'Croatie'),
            ('SI', 'Slovénie'),
            ('SK', 'Slovaquie'),
            ('LT', 'Lituanie'),
            ('LV', 'Lettonie'),
            ('EE', 'Estonie'),
            ('GR', 'Grèce'),
            ('CY', 'Chypre'),
            ('MT', 'Malte'),
            ('LU', 'Luxembourg'),
            
            # Amérique du Nord
            ('US', 'États-Unis'),
            ('CA', 'Canada'),
            ('MX', 'Mexique'),
            
            # Amérique du Sud
            ('BR', 'Brésil'),
            ('AR', 'Argentine'),
            ('CL', 'Chili'),
            ('CO', 'Colombie'),
            ('PE', 'Pérou'),
            ('VE', 'Venezuela'),
            ('EC', 'Équateur'),
            ('BO', 'Bolivie'),
            ('PY', 'Paraguay'),
            ('UY', 'Uruguay'),
            ('GY', 'Guyana'),
            ('SR', 'Suriname'),
            ('GF', 'Guyane française'),
            
            # Asie
            ('CN', 'Chine'),
            ('JP', 'Japon'),
            ('KR', 'Corée du Sud'),
            ('IN', 'Inde'),
            ('TH', 'Thaïlande'),
            ('VN', 'Vietnam'),
            ('ID', 'Indonésie'),
            ('MY', 'Malaisie'),
            ('SG', 'Singapour'),
            ('PH', 'Philippines'),
            ('BD', 'Bangladesh'),
            ('PK', 'Pakistan'),
            ('LK', 'Sri Lanka'),
            ('MM', 'Myanmar'),
            ('KH', 'Cambodge'),
            ('LA', 'Laos'),
            ('BN', 'Brunei'),
            ('TL', 'Timor oriental'),
            
            # Moyen-Orient
            ('AE', 'Émirats arabes unis'),
            ('SA', 'Arabie saoudite'),
            ('QA', 'Qatar'),
            ('KW', 'Koweït'),
            ('BH', 'Bahreïn'),
            ('OM', 'Oman'),
            ('JO', 'Jordanie'),
            ('LB', 'Liban'),
            ('SY', 'Syrie'),
            ('IQ', 'Irak'),
            ('IR', 'Iran'),
            ('IL', 'Israël'),
            ('PS', 'Palestine'),
            ('TR', 'Turquie'),
            
            # Océanie
            ('AU', 'Australie'),
            ('NZ', 'Nouvelle-Zélande'),
            ('FJ', 'Fidji'),
            ('PG', 'Papouasie-Nouvelle-Guinée'),
            ('NC', 'Nouvelle-Calédonie'),
            ('VU', 'Vanuatu'),
            ('SB', 'Salomon'),
            ('TO', 'Tonga'),
            ('WS', 'Samoa'),
            ('KI', 'Kiribati'),
            ('TV', 'Tuvalu'),
            ('NR', 'Nauru'),
            ('PW', 'Palaos'),
            ('FM', 'Micronésie'),
            ('MH', 'Marshall'),
        ],
        'operators': [
            ('MTN', 'MTN'),
            ('Orange', 'Orange'),
            ('Moov', 'Moov'),
            ('Free', 'Free'),
            ('Airtel', 'Airtel'),
            ('Vodacom', 'Vodacom'),
            ('Safaricom', 'Safaricom'),
        ]
    }
    
    return render(request, 'seller_payment_setup.html', context)

@login_required
def reset_payment_info(request):
    payment_info, _ = SellerPaymentInfo.objects.get_or_create(user=request.user)
    payment_info.delete()
    messages.success(request, 'Informations de paiement réinitialisées')
    return redirect('seller_payment_setup')

# ===== HIGHLIGHTS SYSTEM =====

def highlights_home(request):
    """Page d'accueil des Highlights avec navigation"""
    try:
        # Récupérer quelques highlights récents pour l'aperçu
        recent_highlights = Highlight.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'author__profile').order_by('-created_at')[:10]
        
        # Statistiques pour l'utilisateur connecté
        user_stats = {}
        if request.user.is_authenticated:
            user_stats = {
                'highlights_count': Highlight.objects.filter(author=request.user, is_active=True).count(),
                'subscribers_count': request.user.subscribers.count(),
                'subscriptions_count': request.user.subscriptions.count(),
            }
        
        context = {
            'recent_highlights': recent_highlights,
            'user_stats': user_stats,
        }
        return render(request, 'highlights/home.html', context)
    except Exception as e:
        logger.error(f"Erreur highlights_home: {e}")
        messages.error(request, "Erreur lors du chargement des Highlights")
        return redirect('index')

def highlights_for_you(request):
    """Feed personnalisé des Highlights - VERSION OPTIMISÉE pour chargement à la demande"""
    try:
        # Vérifier si on veut accéder à un highlight spécifique
        target_highlight_id = request.GET.get('highlight')
        
        if target_highlight_id:
            # Mode accès direct : utiliser l'API pour charger le contexte
            context = {
                'highlights': [],  # Empty initial load
                'feed_type': 'for_you',
                'target_highlight_id': target_highlight_id,
                'load_mode': 'direct',
                'page_title': 'Highlights',
            }
            return render(request, 'highlights/feed.html', context)
        
        # Mode normal : chargement initial limité (3-5 vidéos)
        initial_limit = 3
        
        base_highlights = Highlight.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'author__profile')
        
        # Appliquer la logique de tri selon l'utilisateur
        if request.user.is_authenticated:
            # Récupérer les IDs des highlights déjà vus par l'utilisateur
            viewed_highlight_ids = HighlightView.objects.filter(
                user=request.user
            ).values_list('highlight_id', flat=True)
            
            # Séparer les highlights vus et non vus
            unviewed_highlights = base_highlights.exclude(
                id__in=viewed_highlight_ids
            ).order_by('-created_at')
            
            viewed_highlights = base_highlights.filter(
                id__in=viewed_highlight_ids
            ).order_by('-created_at')
            
            # Prioriser les abonnements dans les highlights non vus
            subscribed_users = request.user.subscriptions.values_list('subscribed_to', flat=True)
            if subscribed_users:
                unviewed_subscribed = unviewed_highlights.filter(author__in=subscribed_users)
                unviewed_others = unviewed_highlights.exclude(author__in=subscribed_users)
                
                # Priorité : non vus (abonnements + autres) puis vus
                from itertools import chain
                highlights_query = chain(unviewed_subscribed, unviewed_others, viewed_highlights)
                # Convertir en liste et prendre seulement les premiers
                highlights = list(highlights_query)[:initial_limit]
            else:
                from itertools import chain
                highlights_query = chain(unviewed_highlights, viewed_highlights)
                highlights = list(highlights_query)[:initial_limit]
        else:
            # Utilisateur non connecté: tri classique par date, limité
            highlights = list(base_highlights.order_by('-created_at')[:initial_limit])
        
        # Ajouter les informations d'appréciation pour les highlights initiaux
        for highlight in highlights:
            if request.user.is_authenticated:
                highlight.user_appreciation = HighlightAppreciation.objects.filter(
                    highlight=highlight,
                    user=request.user
                ).first()
                highlight.is_viewed = HighlightView.objects.filter(
                    highlight=highlight,
                    user=request.user
                ).exists()
            else:
                highlight.user_appreciation = None
                highlight.is_viewed = False
            
            highlight.appreciation_counts = highlight.get_appreciation_counts_by_level()
        
        context = {
            'highlights': highlights,
            'feed_type': 'for_you',
            'target_highlight_id': None,
            'load_mode': 'initial',
            'page_title': 'Highlights',
        }
        return render(request, 'highlights/feed.html', context)
        
    except Exception as e:
        logger.error(f"Erreur highlights_for_you: {e}")
        messages.error(request, "Erreur lors du chargement du feed")
        return redirect('highlights_for_you')

@login_required
def highlights_friends(request):
    """Highlights des amis/abonnements uniquement"""
    try:
        subscribed_users = request.user.subscriptions.values_list('subscribed_to', flat=True)
        
        highlights = Highlight.objects.filter(
            author__in=subscribed_users,
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'author__profile').prefetch_related(
            'appreciations', 'comments', 'views'
        ).order_by('-created_at')
        
        paginator = Paginator(highlights, 20)
        page_number = request.GET.get('page')
        highlights = paginator.get_page(page_number)
        
        # Ajouter les appréciations utilisateur et compteurs pour chaque highlight
        for highlight in highlights:
            highlight.user_appreciation = HighlightAppreciation.objects.filter(
                highlight=highlight,
                user=request.user
            ).first()
            highlight.appreciation_counts = highlight.get_appreciation_counts_by_level()
        
        context = {
            'highlights': highlights,
            'page_title': 'Amis',
        }
        return render(request, 'highlights/feed.html', context)
    except Exception as e:
        logger.error(f"Erreur highlights_friends: {e}")
        messages.error(request, "Erreur lors du chargement des highlights d'amis")
        return redirect('highlights_for_you')

def highlights_search(request):
    """Recherche de Highlights par hashtags ou utilisateurs"""
    try:
        query = request.GET.get('q', '').strip()
        highlights = Highlight.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'author__profile')
        
        if query:
            if query.startswith('#'):
                # Recherche par hashtag
                hashtag = query[1:].lower()
                highlights = highlights.filter(hashtags__icontains=hashtag)
            else:
                # Recherche par utilisateur ou caption
                highlights = highlights.filter(
                    Q(author__username__icontains=query) |
                    Q(caption__icontains=query)
                )
        
        paginator = Paginator(highlights, 20)
        page_number = request.GET.get('page')
        highlights = paginator.get_page(page_number)
        
        # Hashtags populaires
        popular_hashtags = []
        try:
            all_hashtags = []
            for h in Highlight.objects.filter(is_active=True, expires_at__gt=timezone.now()).values_list('hashtags', flat=True):
                if h:
                    all_hashtags.extend(h)
            
            from collections import Counter
            hashtag_counts = Counter(all_hashtags)
            popular_hashtags = [tag for tag, count in hashtag_counts.most_common(10)]
        except Exception:
            pass
        
        context = {
            'highlights': highlights,
            'query': query,
            'popular_hashtags': popular_hashtags,
            'page_title': 'Recherche',
        }
        return render(request, 'highlights/search.html', context)
    except Exception as e:
        logger.error(f"Erreur highlights_search: {e}")
        messages.error(request, "Erreur lors de la recherche")
        return redirect('highlights_for_you')

def highlights_hashtag(request, hashtag):
    """Highlights pour un hashtag spécifique"""
    try:
        highlights = Highlight.objects.filter(
            hashtags__icontains=hashtag.lower(),
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'author__profile').order_by('-created_at')
        
        paginator = Paginator(highlights, 20)
        page_number = request.GET.get('page')
        highlights = paginator.get_page(page_number)
        
        context = {
            'highlights': highlights,
            'hashtag': hashtag,
            'page_title': f'#{hashtag}',
        }
        return render(request, 'highlights/hashtag.html', context)
    except Exception as e:
        logger.error(f"Erreur highlights_hashtag: {e}")
        messages.error(request, "Erreur lors du chargement du hashtag")
        return redirect('highlights_search')

@login_required
def create_highlight(request):
    """Créer un nouveau Highlight"""
    try:
        if request.method == 'POST':
            video = request.FILES.get('video')
            caption = request.POST.get('caption', '').strip()
            
            if not video:
                messages.error(request, 'Veuillez sélectionner une vidéo')
                return render(request, 'highlights/create.html')
            
            # Extraire les hashtags de la caption
            hashtags = re.findall(r'#(\w+)', caption.lower())
            
            # Créer le highlight
            highlight = Highlight.objects.create(
                author=request.user,
                video=video,
                caption=caption,
                hashtags=hashtags
            )
            
            messages.success(request, 'Highlight créé avec succès!')
            return redirect('highlight_detail', highlight_id=highlight.id)
        
        return render(request, 'highlights/create.html')
    except Exception as e:
        logger.error(f"Erreur create_highlight: {e}")
        messages.error(request, "Erreur lors de la création du Highlight")
        return redirect('highlights_for_you')

def highlight_detail(request, highlight_id):
    """Détail d'un Highlight avec commentaires"""
    try:
        highlight = get_object_or_404(
            Highlight.objects.select_related('author', 'author__profile'),
            id=highlight_id
        )
        
        # Pour les admins examinant un signalement, permettre l'accès même si expiré
        if highlight.is_expired and not request.user.is_staff:
            messages.warning(request, "Ce Highlight a expiré")
            return redirect('highlights_for_you')
        
        # Enregistrer la vue
        if request.user.is_authenticated:
            HighlightView.objects.get_or_create(
                highlight=highlight,
                user=request.user,
                defaults={'ip_address': request.META.get('REMOTE_ADDR')}
            )
        
        # Récupérer les commentaires
        comments = highlight.comments.select_related('user', 'user__profile').order_by('-created_at')
        
        # Vérifier si l'utilisateur a apprécié
        user_appreciation = None
        if request.user.is_authenticated:
            user_appreciation = highlight.appreciations.filter(user=request.user).first()
        
        # Navigation précédent/suivant (par date de création)
        now = timezone.now()
        previous_highlight = Highlight.objects.filter(
            is_active=True,
            expires_at__gt=now,
            created_at__gt=highlight.created_at
        ).order_by('created_at').first()
        next_highlight = Highlight.objects.filter(
            is_active=True,
            expires_at__gt=now,
            created_at__lt=highlight.created_at
        ).order_by('-created_at').first()
        
        context = {
            'highlight': highlight,
            'comments': comments,
            'user_appreciation': user_appreciation,
            'previous_highlight': previous_highlight,
            'next_highlight': next_highlight,
        }
        return render(request, 'highlights/detail.html', context)
    except Exception as e:
        logger.error(f"Erreur highlight_detail: {e}")
        messages.error(request, "Highlight non trouvé")
        # Rediriger vers la page d'origine ou highlights_for_you par défaut
        referer = request.META.get('HTTP_REFERER', '')
        if '/highlights/for-you/' in referer:
            return redirect('highlights_for_you')
        else:
            return redirect('highlights_for_you')

@login_required
def delete_highlight(request, highlight_id):
    """Supprimer un Highlight"""
    try:
        highlight = get_object_or_404(Highlight, id=highlight_id, author=request.user)
        
        if request.method == 'POST':
            highlight.delete()
            messages.success(request, 'Highlight supprimé avec succès')
            return redirect('highlights_for_you')
        
        return render(request, 'highlights/confirm_delete.html', {'highlight': highlight})
    except Exception as e:
        logger.error(f"Erreur delete_highlight: {e}")
        messages.error(request, "Erreur lors de la suppression")
        return redirect('highlights_for_you')

@login_required
@require_POST
def toggle_highlight_appreciation(request, highlight_id):
    """Ajouter ou modifier l'appréciation d'un highlight"""
    try:
        highlight = get_object_or_404(Highlight, id=highlight_id, is_active=True)
        appreciation_level = int(request.POST.get('appreciation_level', 0))
        
        if appreciation_level not in [1, 2, 3, 4, 5, 6]:
            return JsonResponse({'error': 'Niveau d\'appréciation invalide'}, status=400)
        
        # Vérifier si l'utilisateur a déjà apprécié
        existing_appreciation = HighlightAppreciation.objects.filter(
            highlight=highlight,
            user=request.user
        ).first()
        
        if existing_appreciation:
            # Mettre à jour l'appréciation existante
            old_level = existing_appreciation.appreciation_level
            existing_appreciation.appreciation_level = appreciation_level
            existing_appreciation.save()
            
            # Mettre à jour le score de l'auteur
            author_profile = highlight.author.profile
            # Annuler l'ancien impact
            old_impact = {
                1: -10, 2: -4, 3: 2, 4: 4, 5: 6, 6: 10
            }.get(old_level, 0)
            # Ajouter le nouvel impact
            new_impact = {
                1: -10, 2: -4, 3: 2, 4: 4, 5: 6, 6: 10
            }.get(appreciation_level, 0)
            
            author_profile.score = author_profile.score - old_impact + new_impact
            author_profile.save()
            
        else:
            # Créer une nouvelle appréciation
            HighlightAppreciation.objects.create(
                highlight=highlight,
                user=request.user,
                appreciation_level=appreciation_level
            )
            
            # Mettre à jour le score de l'auteur
            author_profile = highlight.author.profile
            author_profile.update_score_from_appreciation(appreciation_level)
        
        # Calculer les statistiques d'appréciation
        appreciations = highlight.appreciations.all()
        appreciation_stats = {}
        for level in range(1, 7):
            count = appreciations.filter(appreciation_level=level).count()
            appreciation_stats[f'level_{level}'] = count
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'appreciation_level': appreciation_level,
                'appreciation_stats': appreciation_stats,
                'total_appreciations': appreciations.count()
            })
        
        return redirect('highlight_detail', highlight_id=highlight.id)
    except Exception as e:
        logger.error(f"Erreur toggle_highlight_appreciation: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def add_highlight_comment(request, highlight_id):
    """Ajouter un commentaire à un Highlight"""
    try:
        highlight = get_object_or_404(Highlight, id=highlight_id, is_active=True)
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Commentaire vide'})
        
        comment = HighlightComment.objects.create(
            highlight=highlight,
            user=request.user,
            content=content
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': str(comment.id),
                    'content': comment.content,
                    'user': comment.user.username,
                    'created_at': comment.created_at.strftime('%H:%M'),
                    'user_avatar': comment.user.profile.profileimg.url if hasattr(comment.user, 'profile') and comment.user.profile.profileimg else None
                },
                'comments_count': highlight.comments_count
            })
        
        return redirect('highlight_detail', highlight_id=highlight.id)
    except Exception as e:
        logger.error(f"Erreur add_highlight_comment: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def share_highlight(request, highlight_id):
    """Partager un Highlight"""
    try:
        highlight = get_object_or_404(Highlight, id=highlight_id, is_active=True)
        shared_to_id = request.POST.get('shared_to')
        
        shared_to = None
        if shared_to_id:
            shared_to = get_object_or_404(User, id=shared_to_id)
        
        share = HighlightShare.objects.create(
            highlight=highlight,
            user=request.user,
            shared_to=shared_to
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Highlight partagé'})
        
        messages.success(request, 'Highlight partagé avec succès')
        return redirect('highlight_detail', highlight_id=highlight.id)
    except Exception as e:
        logger.error(f"Erreur share_highlight: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def record_highlight_view(request, highlight_id):
    """Enregistrer une vue sur un Highlight"""
    try:
        highlight = get_object_or_404(Highlight, id=highlight_id, is_active=True)
        
        if request.user.is_authenticated:
            view, created = HighlightView.objects.get_or_create(
                highlight=highlight,
                user=request.user,
                defaults={'ip_address': request.META.get('REMOTE_ADDR')}
            )
        else:
            # Pour les utilisateurs anonymes, utiliser l'IP
            ip_address = request.META.get('REMOTE_ADDR')
            if ip_address:
                view, created = HighlightView.objects.get_or_create(
                    highlight=highlight,
                    ip_address=ip_address,
                    user=None
                )
        
        return JsonResponse({'success': True, 'views_count': highlight.views.count()})
    except Exception as e:
        logger.error(f"Erreur record_highlight_view: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def toggle_subscription(request, user_id):
    """S'abonner/Se désabonner d'un utilisateur"""
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        if target_user == request.user:
            return JsonResponse({'success': False, 'error': 'Impossible de s\'abonner à soi-même'})
        
        subscription, created = UserSubscription.objects.get_or_create(
            subscriber=request.user,
            subscribed_to=target_user
        )
        
        if not created:
            subscription.delete()
            subscribed = False
            action = 'désabonné'
        else:
            subscribed = True
            action = 'abonné'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'subscribed': subscribed,
                'action': action,
                'subscribers_count': target_user.subscribers.count()
            })
        
        messages.success(request, f'Vous êtes maintenant {action} à {target_user.username}')
        return redirect('profile', username=target_user.username)
    except Exception as e:
        logger.error(f"Erreur toggle_subscription: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def my_subscriptions(request):
    """Liste des abonnements de l'utilisateur"""
    try:
        subscriptions = UserSubscription.objects.filter(
            subscriber=request.user
        ).select_related('subscribed_to', 'subscribed_to__profile').order_by('-created_at')
        
        context = {
            'subscriptions': subscriptions,
        }
        return render(request, 'highlights/subscriptions.html', context)
    except Exception as e:
        logger.error(f"Erreur my_subscriptions: {e}")
        messages.error(request, "Erreur lors du chargement des abonnements")
        return redirect('highlights_for_you')

@login_required
def my_subscribers(request):
    """Liste des abonnés de l'utilisateur"""
    try:
        subscribers = UserSubscription.objects.filter(
            subscribed_to=request.user
        ).select_related('subscriber', 'subscriber__profile').order_by('-created_at')
        
        context = {
            'subscribers': subscribers,
        }
        return render(request, 'highlights/subscribers.html', context)
    except Exception as e:
        logger.error(f"Erreur my_subscribers: {e}")
        messages.error(request, "Erreur lors du chargement des abonnés")
        return redirect('highlights_for_you')

# ===== API HIGHLIGHTS (AJAX) =====

def highlights_feed_api(request):
    """API pour le feed des Highlights (AJAX) avec analytics - VERSION OPTIMISÉE"""
    try:
        # Paramètres de pagination optimisés pour TikTok-like feed
        limit = int(request.GET.get('limit', 5))  # Par défaut 5 vidéos au lieu de 10
        offset = int(request.GET.get('offset', 0))  # Offset au lieu de page
        feed_type = request.GET.get('type', 'for_you')
        
        # Limiter le nombre maximum pour éviter la surcharge
        limit = min(limit, 10)
        
        highlights = Highlight.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'author__profile').prefetch_related(
            'appreciations', 'comments', 'views'
        )
        
        # Smart discovery algorithm
        if feed_type == 'for_you' and request.user.is_authenticated:
            # Prioritize based on user engagement patterns
            user_liked_hashtags = get_user_preferred_hashtags(request.user)
            user_interactions = get_user_interaction_history(request.user)
            
            # Apply intelligent sorting
            highlights = apply_discovery_algorithm(highlights, request.user, user_liked_hashtags, user_interactions)
        elif feed_type == 'friends' and request.user.is_authenticated:
            subscribed_users = request.user.subscriptions.values_list('subscribed_to', flat=True)
            highlights = highlights.filter(author__in=subscribed_users)
        
        highlights = highlights.order_by('-created_at')
        
        # Utiliser offset/limit au lieu de pagination Django
        total_count = highlights.count()
        highlights_slice = highlights[offset:offset + limit]
        
        highlights_data = []
        for highlight in highlights_slice:
            user_appreciated = None
            appreciation_counts = {}
            if request.user.is_authenticated:
                user_appreciated = highlight.appreciations.filter(user=request.user).first()
            
            # Récupérer les compteurs d'appréciations par niveau
            appreciation_counts = highlight.get_appreciation_counts_by_level()
            
            # Enhanced analytics data
            engagement_rate = calculate_engagement_rate(highlight)
            view_duration_avg = get_average_view_duration(highlight)
            
            highlights_data.append({
                'id': str(highlight.id),
                'video_url': highlight.video.url,
                'caption': highlight.caption,
                'hashtags': highlight.hashtags,
                'author': {
                    'id': highlight.author.id,
                    'username': highlight.author.username,
                    'avatar': highlight.author.profile.profileimg.url if hasattr(highlight.author, 'profile') and highlight.author.profile.profileimg else None
                },
                'appreciations_count': highlight.appreciations_count,
                'appreciation_counts': appreciation_counts,
                'comments_count': highlight.comments_count,
                'views_count': highlight.views.count(),
                'user_appreciation': {
                    'appreciation_level': user_appreciated.appreciation_level if user_appreciated else None
                },
                'created_at': highlight.created_at.strftime('%H:%M'),
                'time_remaining': str(highlight.time_remaining) if highlight.time_remaining else None,
                'engagement_rate': engagement_rate,
                'avg_view_duration': view_duration_avg,
                'performance_score': calculate_performance_score(highlight)
            })
        
        return JsonResponse({
            'success': True,
            'highlights': highlights_data,
            'has_more': offset + limit < total_count,
            'next_offset': offset + limit if offset + limit < total_count else None,
            'total_count': total_count,
            'analytics': {
                'avg_engagement': calculate_average_engagement(highlights_slice),
                'trending_hashtags': get_trending_hashtags()
            }
        })
    except Exception as e:
        logger.error(f"Erreur highlights_feed_api: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def highlights_context_api(request, highlight_id):
    """API pour accéder directement à un highlight avec contexte (TikTok-like)"""
    try:
        # Récupérer le highlight cible
        target_highlight = get_object_or_404(
            Highlight.objects.select_related('author', 'author__profile'),
            id=highlight_id,
            is_active=True,
            expires_at__gt=timezone.now()
        )
        
        # Paramètres pour le contexte
        context_before = int(request.GET.get('before', 2))  # 2 vidéos avant
        context_after = int(request.GET.get('after', 3))    # 3 vidéos après
        feed_type = request.GET.get('type', 'for_you')
        
        # Limiter les paramètres pour éviter la surcharge
        context_before = min(context_before, 5)
        context_after = min(context_after, 5)
        
        # Base query pour tous les highlights
        base_highlights = Highlight.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'author__profile')
        
        # Appliquer la logique de feed selon le type
        if feed_type == 'for_you' and request.user.is_authenticated:
            user_liked_hashtags = get_user_preferred_hashtags(request.user)
            user_interactions = get_user_interaction_history(request.user)
            base_highlights = apply_discovery_algorithm(base_highlights, request.user, user_liked_hashtags, user_interactions)
        elif feed_type == 'friends' and request.user.is_authenticated:
            subscribed_users = request.user.subscriptions.values_list('subscribed_to', flat=True)
            base_highlights = base_highlights.filter(author__in=subscribed_users)
        
        base_highlights = base_highlights.order_by('-created_at')
        
        # Trouver la position du highlight cible dans le feed ordonné
        target_position = None
        highlights_before_target = []
        highlights_after_target = []
        
        # Récupérer les highlights avant le target
        before_highlights = base_highlights.filter(
            created_at__gt=target_highlight.created_at
        ).order_by('created_at')[:context_before]
        highlights_before_target = list(reversed(before_highlights))
        
        # Récupérer les highlights après le target
        after_highlights = base_highlights.filter(
            created_at__lt=target_highlight.created_at
        ).order_by('-created_at')[:context_after]
        highlights_after_target = list(after_highlights)
        
        # Combiner tous les highlights : avant + target + après
        all_highlights = highlights_before_target + [target_highlight] + highlights_after_target
        
        # Position du target dans la liste combinée
        target_index = len(highlights_before_target)
        
        # Préparer les données
        highlights_data = []
        for highlight in all_highlights:
            user_appreciated = None
            appreciation_counts = {}
            if request.user.is_authenticated:
                user_appreciated = highlight.appreciations.filter(user=request.user).first()
            
            appreciation_counts = highlight.get_appreciation_counts_by_level()
            
            highlights_data.append({
                'id': str(highlight.id),
                'video_url': highlight.video.url,
                'caption': highlight.caption,
                'hashtags': highlight.hashtags,
                'author': {
                    'id': highlight.author.id,
                    'username': highlight.author.username,
                    'avatar': highlight.author.profile.profileimg.url if hasattr(highlight.author, 'profile') and highlight.author.profile.profileimg else None
                },
                'appreciations_count': highlight.appreciations_count,
                'appreciation_counts': appreciation_counts,
                'comments_count': highlight.comments_count,
                'views_count': highlight.views.count(),
                'user_appreciation': {
                    'appreciation_level': user_appreciated.appreciation_level if user_appreciated else None
                },
                'created_at': highlight.created_at.strftime('%H:%M'),
                'time_remaining': str(highlight.time_remaining) if highlight.time_remaining else None,
                'is_target': highlight.id == target_highlight.id
            })
        
        return JsonResponse({
            'success': True,
            'highlights': highlights_data,
            'target_index': target_index,
            'target_id': str(target_highlight.id),
            'context': {
                'before': len(highlights_before_target),
                'after': len(highlights_after_target)
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur highlights_context_api: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def highlight_comments_api(request, highlight_id):
    """API pour les commentaires d'un Highlight"""
    try:
        highlight = get_object_or_404(Highlight, id=highlight_id, is_active=True)
        comments = highlight.comments.select_related('user', 'user__profile').order_by('-created_at')
        
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': str(comment.id),
                'content': comment.content,
                'user': {
                    'username': comment.user.username,
                    'avatar': comment.user.profile.profileimg.url if hasattr(comment.user, 'profile') and comment.user.profile.profileimg else None
                },
                'created_at': comment.created_at.strftime('%H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'comments': comments_data
        })
    except Exception as e:
        logger.error(f"Erreur highlight_comments_api: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

# ===== ANALYTICS AND PERFORMANCE HELPERS =====

def get_user_preferred_hashtags(user, limit=10):
    """Get user's preferred hashtags based on interaction history"""
    try:
        # Get hashtags from highlights the user liked
        liked_highlights = Highlight.objects.filter(
            appreciations__user=user,
            is_active=True
        ).values_list('hashtags', flat=True)
        
        all_hashtags = []
        for hashtag_list in liked_highlights:
            if hashtag_list:
                all_hashtags.extend(hashtag_list)
        
        from collections import Counter
        hashtag_counts = Counter(all_hashtags)
        return [tag for tag, count in hashtag_counts.most_common(limit)]
    except Exception as e:
        logger.error(f"Error getting user preferred hashtags: {e}")
        return []

def get_user_interaction_history(user):
    """Get user's interaction patterns for recommendation algorithm"""
    try:
        from django.db.models import Count
        
        # Get users the current user interacts with most
        interacted_users = User.objects.filter(
            Q(highlights__appreciations__user=user) |
            Q(highlights__comments__user=user)
        ).annotate(
            interaction_count=Count('highlights__appreciations') + Count('highlights__comments')
        ).order_by('-interaction_count')[:20]
        
        return list(interacted_users.values_list('id', flat=True))
    except Exception as e:
        logger.error(f"Error getting user interaction history: {e}")
        return []

def apply_discovery_algorithm(highlights_queryset, user, preferred_hashtags, interaction_users):
    """Apply smart discovery algorithm to sort highlights"""
    try:
        from django.db.models import Case, When, IntegerField, F
        
        # Create scoring conditions
        hashtag_score = Case(
            *[When(hashtags__icontains=tag, then=5) for tag in preferred_hashtags[:5]],
            default=0,
            output_field=IntegerField()
        )
        
        interaction_score = Case(
            When(author__id__in=interaction_users[:10], then=3),
            default=0,
            output_field=IntegerField()
        )
        
        # Apply scoring and sort
        return highlights_queryset.annotate(
            discovery_score=hashtag_score + interaction_score
        ).order_by('-discovery_score', '-created_at')
        
    except Exception as e:
        logger.error(f"Error applying discovery algorithm: {e}")
        return highlights_queryset.order_by('-created_at')

def calculate_engagement_rate(highlight):
    """Calculate engagement rate for a highlight"""
    try:
        views_count = highlight.views.count()
        if views_count == 0:
            return 0.0
        
        engagements = highlight.appreciations_count + highlight.comments_count
        return round((engagements / views_count) * 100, 2)
    except Exception as e:
        logger.error(f"Error calculating engagement rate: {e}")
        return 0.0

def get_average_view_duration(highlight):
    """Get average view duration for a highlight (placeholder for future implementation)"""
    # This would require tracking actual view durations
    # For now, return a simulated value based on engagement
    try:
        base_duration = 8.0  # seconds
        engagement_multiplier = min(calculate_engagement_rate(highlight) / 10, 2.0)
        return round(base_duration * (1 + engagement_multiplier), 1)
    except Exception:
        return 8.0

def calculate_performance_score(highlight):
    """Calculate overall performance score for a highlight"""
    try:
        engagement_rate = calculate_engagement_rate(highlight)
        views_count = highlight.views.count()
        recency_score = max(0, 100 - (timezone.now() - highlight.created_at).days * 10)
        
        # Weighted score calculation
        score = (
            engagement_rate * 0.4 +  # 40% engagement
            min(views_count / 10, 50) * 0.3 +  # 30% views (capped at 50)
            recency_score * 0.3  # 30% recency
        )
        
        return round(score, 1)
    except Exception as e:
        logger.error(f"Error calculating performance score: {e}")
        return 0.0

def calculate_average_engagement(highlights_page):
    """Calculate average engagement for a page of highlights"""
    try:
        if not highlights_page:
            return 0.0
        
        total_engagement = sum(calculate_engagement_rate(h) for h in highlights_page)
        return round(total_engagement / len(highlights_page), 2)
    except Exception as e:
        logger.error(f"Error calculating average engagement: {e}")
        return 0.0

def get_trending_hashtags(limit=10):
    """Get currently trending hashtags with engagement scoring"""
    try:
        from collections import Counter
        
        # Get hashtags from recent highlights (last 24 hours) with engagement data
        recent_highlights = Highlight.objects.filter(
            is_active=True,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).prefetch_related('appreciations', 'views', 'comments')
        
        hashtag_scores = {}
        
        for highlight in recent_highlights:
            if not highlight.hashtags:
                continue
            
            # Calculate engagement score
            engagement_score = (
                highlight.appreciations.count() * 3 +
                highlight.views.count() * 1 +
                highlight.comments.count() * 2
            )
            
            for hashtag in highlight.hashtags:
                hashtag_lower = hashtag.lower()
                if hashtag_lower not in hashtag_scores:
                    hashtag_scores[hashtag_lower] = {'score': 0, 'count': 0}
                hashtag_scores[hashtag_lower]['score'] += engagement_score + 1
                hashtag_scores[hashtag_lower]['count'] += 1
        
        # Sort by engagement score
        trending = sorted(
            hashtag_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )[:limit]
        
        return [
            {
                'tag': tag, 
                'score': data['score'], 
                'count': data['count'],
                'engagement_rate': round(data['score'] / data['count'], 1) if data['count'] > 0 else 0
            } 
            for tag, data in trending
        ]
    except Exception as e:
        logger.error(f"Error getting trending hashtags: {e}")
        return []

# API endpoint for hashtag suggestions
@require_http_methods(["GET"])
def hashtag_suggestions_api(request):
    """API endpoint pour récupérer les suggestions de hashtags"""
    try:
        # Hashtags tendances
        trending = get_trending_hashtags(10)
        
        # Hashtags populaires (30 derniers jours)
        popular_hashtags = []
        try:
            all_hashtags = []
            for h in Highlight.objects.filter(
                is_active=True, 
                created_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).values_list('hashtags', flat=True):
                if h:
                    all_hashtags.extend(h)
            
            from collections import Counter
            hashtag_counts = Counter(all_hashtags)
            popular_hashtags = [
                {'tag': tag, 'count': count} 
                for tag, count in hashtag_counts.most_common(15)
                if count >= 3
            ]
        except Exception:
            pass
        
        # Hashtags gaming spécifiques
        gaming_keywords = [
            'gaming', 'game', 'play', 'win', 'victory', 'clutch', 'epic', 'pro',
            'kill', 'headshot', 'ace', 'mvp', 'team', 'solo', 'duo', 'squad',
            'freefire', 'pubg', 'fortnite', 'valorant', 'lol', 'cod', 'mobile'
        ]
        
        gaming_hashtags = [
            item for item in popular_hashtags 
            if any(keyword in item['tag'].lower() for keyword in gaming_keywords)
        ][:10]
        
        suggestions = {
            'trending': trending,
            'popular': popular_hashtags,
            'gaming': gaming_hashtags
        }
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Erreur API suggestions hashtags: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors du chargement des suggestions'
        })

# Enhanced view recording with duration tracking
@require_POST
def record_highlight_view_enhanced(request, highlight_id):
    """Enhanced view recording with duration and analytics"""
    try:
        highlight = get_object_or_404(Highlight, id=highlight_id, is_active=True)
        view_duration = request.POST.get('duration', 0)  # Duration in seconds
        
        if request.user.is_authenticated:
            view, created = HighlightView.objects.get_or_create(
                highlight=highlight,
                user=request.user,
                defaults={
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'view_duration': float(view_duration) if view_duration else 0
                }
            )
            
            # Update duration if view already exists
            if not created and view_duration:
                view.view_duration = max(view.view_duration or 0, float(view_duration))
                view.save()
        else:
            # For anonymous users, use IP
            ip_address = request.META.get('REMOTE_ADDR')
            if ip_address:
                view, created = HighlightView.objects.get_or_create(
                    highlight=highlight,
                    ip_address=ip_address,
                    user=None,
                    defaults={'view_duration': float(view_duration) if view_duration else 0}
                )
        
        return JsonResponse({
            'success': True,
            'views_count': highlight.views.count(),
            'engagement_rate': calculate_engagement_rate(highlight)
        })
    except Exception as e:
        logger.error(f"Erreur record_highlight_view_enhanced: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


# ===== VUES ADMIN POUR RÉSOLUTION DES LITIGES =====

@staff_member_required
def admin_dispute_resolve_refund(request, dispute_id):
    """
    Vue admin pour résoudre un litige en faveur de l'acheteur (remboursement)
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    if request.method == 'POST':
        logger.info(f"[DISPUTE REFUND] Début du traitement du litige {dispute_id}")
        try:
            # Utiliser l'API de résolution des litiges
            resolution_api = DisputeResolutionAPI()
            logger.info(f"[DISPUTE REFUND] API de résolution initialisée pour le litige {dispute_id}")
            result = resolution_api.process_refund(dispute)
            logger.info(f"[DISPUTE REFUND] Résultat de l'API: {result}")
            
            if result['success']:
                # Créer notifications pour les parties impliquées
                _create_dispute_resolution_notifications(dispute, 'refund', result.get('refund_id'))
                
                # Gérer le statut de l'annonce après remboursement
                try:
                    from .post_management import handle_dispute_resolution_post_status
                    handle_dispute_resolution_post_status(dispute)
                    logger.info(f"Statut de l'annonce géré pour le litige {dispute.id} (remboursement)")
                except Exception as e:
                    logger.error(f"Erreur lors de la gestion du statut de l'annonce pour le litige {dispute.id}: {e}")
                    # Ne pas faire échouer la résolution si la gestion de l'annonce échoue
                
                # Message différencié selon le mode
                if result.get('test_mode'):
                    messages.success(request, f'🧪 [MODE TEST] Remboursement simulé avec succès. ID: {result["refund_id"]}')
                elif result.get('manual_mode'):
                    messages.success(request, f'✅ PayoutRequest créée avec succès. ID: {result["refund_id"]} - En attente de traitement manuel')
                else:
                    messages.success(request, f'Remboursement effectué avec succès. ID: {result["refund_id"]}')
                
                # Rediriger vers la page de suivi pour gérer les sanctions
                return redirect('admin_dispute_followup', dispute_id=dispute.id)
            else:
                messages.error(request, f'Erreur lors du remboursement: {result["error"]}')
                
        except Exception as e:
            logger.error(f"Erreur lors de la résolution de litige (remboursement): {e}")
            messages.error(request, 'Erreur interne lors du traitement du remboursement')
    
    context = {
        'dispute': dispute,
        'transaction': dispute.transaction,
        'refund_amount': dispute.refund_amount or dispute.disputed_amount,
    }
    return render(request, 'admin/dispute_resolve_refund.html', context)

@staff_member_required
def admin_dispute_resolve_payout(request, dispute_id):
    """
    Vue admin pour résoudre un litige en faveur du vendeur (payout)
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    if request.method == 'POST':
        logger.info(f"[DISPUTE PAYOUT] Début du traitement du litige {dispute_id}")
        try:
            # Utiliser l'API de résolution des litiges
            resolution_api = DisputeResolutionAPI()
            logger.info(f"[DISPUTE PAYOUT] API de résolution initialisée pour le litige {dispute_id}")
            result = resolution_api.process_payout(dispute)
            logger.info(f"[DISPUTE PAYOUT] Résultat de l'API: {result}")
            
            if result['success']:
                # Créer notifications pour les parties impliquées
                _create_dispute_resolution_notifications(dispute, 'payout', result.get('payout_id'))
                
                # Gérer le statut de l'annonce après paiement vendeur
                try:
                    from .post_management import handle_dispute_resolution_post_status
                    handle_dispute_resolution_post_status(dispute)
                    logger.info(f"Statut de l'annonce géré pour le litige {dispute.id} (payout)")
                except Exception as e:
                    logger.error(f"Erreur lors de la gestion du statut de l'annonce pour le litige {dispute.id}: {e}")
                    # Ne pas faire échouer la résolution si la gestion de l'annonce échoue
                
                # Message différencié selon le mode
                if result.get('test_mode'):
                    messages.success(request, f'🧪 [MODE TEST] Paiement vendeur simulé avec succès. ID: {result["payout_id"]}')
                elif result.get('manual_mode'):
                    messages.success(request, f'✅ PayoutRequest créée avec succès. ID: {result["payout_id"]} - En attente de traitement manuel')
                else:
                    messages.success(request, f'Paiement vendeur effectué avec succès. ID: {result["payout_id"]}')
                
                # Rediriger vers la page de suivi pour gérer les sanctions
                return redirect('admin_dispute_followup', dispute_id=dispute.id)
            else:
                messages.error(request, f'Erreur lors du paiement: {result["error"]}')
                
        except Exception as e:
            logger.error(f"Erreur lors de la résolution de litige (payout): {e}")
            messages.error(request, 'Erreur interne lors du traitement du paiement')
    
    context = {
        'dispute': dispute,
        'transaction': dispute.transaction,
        'seller_amount': float(dispute.disputed_amount) * 0.90,
        'commission': float(dispute.disputed_amount) * 0.10,
    }
    return render(request, 'admin/dispute_resolve_payout.html', context)

@staff_member_required
def admin_dispute_dashboard(request):
    """
    Dashboard principal pour la gestion des litiges par les administrateurs
    """
    # Statistiques générales
    total_disputes = Dispute.objects.count()
    pending_disputes = Dispute.objects.filter(status='pending').count()
    investigating_disputes = Dispute.objects.filter(status='investigating').count()
    awaiting_evidence_disputes = Dispute.objects.filter(status='awaiting_evidence').count()
    resolved_disputes = Dispute.objects.filter(
        status__in=['resolved_buyer', 'resolved_seller']
    ).count()
    closed_disputes = Dispute.objects.filter(status='closed').count()
    
    # Calcul du temps moyen de résolution
    resolved_with_time = Dispute.objects.filter(
        status__in=['resolved_buyer', 'resolved_seller'],
        resolution_time_hours__isnull=False
    )
    avg_resolution_time = resolved_with_time.aggregate(
        avg_time=models.Avg('resolution_time_hours')
    )['avg_time'] or 0
    
    # Calcul du temps moyen de première réponse
    avg_response_time = Dispute.objects.filter(
        response_time_hours__isnull=False
    ).aggregate(
        avg_time=models.Avg('response_time_hours')
    )['avg_time'] or 0
    
    # Litiges en retard (> 72h)
    from django.utils import timezone
    overdue_disputes = Dispute.objects.filter(
        deadline__lt=timezone.now(),
        status__in=['pending', 'investigating', 'awaiting_evidence']
    ).count()
    
    # Filtres
    disputes = Dispute.objects.select_related(
        'transaction__post', 'opened_by', 'assigned_admin'
    ).order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        disputes = disputes.filter(status=status_filter)
    
    priority_filter = request.GET.get('priority')
    if priority_filter:
        disputes = disputes.filter(priority=priority_filter)
    
    assigned_filter = request.GET.get('assigned')
    if assigned_filter == 'unassigned':
        disputes = disputes.filter(assigned_admin__isnull=True)
    elif assigned_filter:
        disputes = disputes.filter(assigned_admin_id=assigned_filter)
    
    # Limiter à 50 résultats
    disputes = disputes[:50]
    
    # Liste des admins pour le filtre
    admins = User.objects.filter(is_staff=True)
    
    context = {
        'stats': {
            'total_disputes': total_disputes,
            'pending_disputes': pending_disputes,
            'investigating_disputes': investigating_disputes,
            'awaiting_evidence_disputes': awaiting_evidence_disputes,
            'resolved_disputes': resolved_disputes,
            'closed_disputes': closed_disputes,
            'overdue_disputes': overdue_disputes,
            'avg_resolution_time': avg_resolution_time,
            'avg_response_time': avg_response_time,
        },
        'disputes': disputes,
        'admins': admins,
    }
    
    return render(request, 'admin/dispute_admin_dashboard.html', context)

@staff_member_required
def admin_dispute_detail(request, dispute_id):
    """
    Vue détaillée d'un litige pour les administrateurs
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    # Marquer comme vu par l'admin si pas encore assigné
    if not dispute.assigned_admin and not dispute.response_time_hours:
        dispute.response_time_hours = int(
            (timezone.now() - dispute.created_at).total_seconds() / 3600
        )
        dispute.save()
    
    # Statistiques de litiges pour l'acheteur
    buyer_stats = {
        'total_disputes_as_buyer': Dispute.objects.filter(
            transaction__buyer=dispute.transaction.buyer
        ).count(),
        'total_disputes_as_seller': Dispute.objects.filter(
            transaction__seller=dispute.transaction.buyer
        ).count(),
        'disputes_lost_as_buyer': Dispute.objects.filter(
            transaction__buyer=dispute.transaction.buyer,
            resolution='seller_favored'
        ).count(),
        'disputes_lost_as_seller': Dispute.objects.filter(
            transaction__seller=dispute.transaction.buyer,
            resolution='buyer_favored'
        ).count(),
    }
    
    # Statistiques de litiges pour le vendeur
    seller_stats = {
        'total_disputes_as_buyer': Dispute.objects.filter(
            transaction__buyer=dispute.transaction.seller
        ).count(),
        'total_disputes_as_seller': Dispute.objects.filter(
            transaction__seller=dispute.transaction.seller
        ).count(),
        'disputes_lost_as_buyer': Dispute.objects.filter(
            transaction__buyer=dispute.transaction.seller,
            resolution='seller_favored'
        ).count(),
        'disputes_lost_as_seller': Dispute.objects.filter(
            transaction__seller=dispute.transaction.seller,
            resolution='buyer_favored'
        ).count(),
    }
    
    # Récupérer les messages de la transaction (nouveau système Pusher)
    messages_list = []
    try:
        # Récupérer le chat de la transaction
        chat = Chat.objects.get(transaction=dispute.transaction)
        messages_list = chat.messages.select_related('sender').order_by('created_at')
    except Chat.DoesNotExist:
        # Si pas de chat, créer un chat vide pour la transaction
        chat = Chat.objects.create(transaction=dispute.transaction)
        messages_list = []
    
    # Récupérer les messages du litige
    dispute_messages = dispute.messages.all().order_by('created_at')
    
    context = {
        'dispute': dispute,
        'buyer_stats': buyer_stats,
        'seller_stats': seller_stats,
        'messages_list': messages_list,
        'dispute_messages': dispute_messages,
    }
    
    return render(request, 'admin/dispute_detail_admin.html', context)

# Nouvelles vues admin personnalisées
@staff_member_required
def admin_assign_dispute(request, dispute_id):
    """
    Assigner un litige à l'admin connecté
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    if request.method == 'POST':
        dispute.assigned_admin = request.user
        dispute.status = 'in_progress'
        if not dispute.response_time_hours:
            dispute.response_time_hours = int(
                (timezone.now() - dispute.created_at).total_seconds() / 3600
            )
        dispute.save()
        
        messages.success(request, f'Litige #{dispute.id.hex[:8]} assigné avec succès.')
        return redirect('admin_dispute_detail', dispute_id=dispute.id)
    
    return redirect('admin_dispute_dashboard')

@staff_member_required
def admin_update_dispute_notes(request, dispute_id):
    """
    Mettre à jour les notes administratives
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        dispute.admin_notes = admin_notes
        dispute.save()
        
        messages.success(request, 'Notes administratives mises à jour.')
    
    return redirect('admin_dispute_detail', dispute_id=dispute.id)

@staff_member_required
def admin_send_information_request(request, dispute_id):
    """
    Envoyer une demande d'information à l'acheteur ou vendeur
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    if request.method == 'POST':
        requested_to_id = request.POST.get('requested_to')
        request_type = request.POST.get('request_type')
        question = request.POST.get('question')
        
        if not all([requested_to_id, request_type, question]):
            messages.error(request, 'Tous les champs sont requis.')
            return redirect('admin_dispute_detail', dispute_id=dispute.id)
        
        requested_to = get_object_or_404(User, id=requested_to_id)
        
        # Créer la demande d'information
        info_request = DisputeInformationRequest.objects.create(
            dispute=dispute,
            requested_by=request.user,
            requested_to=requested_to,
            request_type=request_type,
            question=question,
            deadline=timezone.now() + timezone.timedelta(hours=24)
        )
        
        # Créer une notification
        Notification.objects.create(
            user=requested_to,
            type='dispute_message',
            title='Demande d\'information - Litige',
            content=f'Un administrateur demande des informations concernant le litige #{dispute.id.hex[:8]}: {question}',
            dispute=dispute
        )
        
        messages.success(request, f'Demande envoyée à {requested_to.username}.')
        return redirect('admin_dispute_detail', dispute_id=dispute.id)
    
    return redirect('admin_dispute_detail', dispute_id=dispute.id)

@login_required
def respond_to_information_request(request, request_id):
    """
    Répondre à une demande d'information
    """
    info_request = get_object_or_404(DisputeInformationRequest, id=request_id, requested_to=request.user)
    
    if info_request.status != 'pending':
        messages.error(request, 'Cette demande a déjà été traitée.')
        return redirect('transaction_detail', transaction_id=info_request.dispute.transaction.id)
    
    if request.method == 'POST':
        if info_request.request_type == 'text_response':
            response_text = request.POST.get('response_text')
            if response_text:
                info_request.response_text = response_text
                info_request.status = 'responded'
                info_request.responded_at = timezone.now()
                info_request.save()
                
                # Notification à l'admin
                Notification.objects.create(
                    user=info_request.requested_by,
                    type='dispute_message',
                    title='Réponse reçue',
                    content=f'{request.user.username} a répondu à votre demande d\'information',
                    dispute=info_request.dispute
                )
                
                messages.success(request, 'Votre réponse a été envoyée.')
            else:
                messages.error(request, 'Veuillez fournir une réponse.')
        else:
            # Pour screenshot/document
            response_file = request.FILES.get('response_file')
            if response_file:
                info_request.response_file = response_file
                info_request.response_text = request.POST.get('response_text', '')
                info_request.status = 'responded'
                info_request.responded_at = timezone.now()
                info_request.save()
                
                # Notification à l'admin
                Notification.objects.create(
                    user=info_request.requested_by,
                    type='dispute_message',
                    title='Fichier reçu',
                    content=f'{request.user.username} a envoyé un fichier en réponse',
                    dispute=info_request.dispute
                )
                
                messages.success(request, 'Votre fichier a été envoyé.')
            else:
                messages.error(request, 'Veuillez joindre un fichier.')
        
        return redirect('transaction_detail', transaction_id=info_request.dispute.transaction.id)
    
    context = {
        'info_request': info_request,
        'dispute': info_request.dispute,
    }
    return render(request, 'respond_information_request.html', context)

@staff_member_required
def admin_access_page(request):
    """
    Page d'accès centralisée pour les admins
    """
    return render(request, 'dispute_admin_access.html')


# ===== FONCTIONS UTILITAIRES POUR NOTIFICATIONS =====

def _create_dispute_resolution_notifications(dispute, resolution_type, transaction_id):
    """
    Créer des notifications automatiques lors de la résolution d'un litige
    """
    try:
        if resolution_type == 'refund':
            # Notification pour l'acheteur (remboursement)
            Notification.objects.create(
                user=dispute.transaction.buyer,
                type='dispute_resolved',
                title='Litige résolu en votre faveur',
                content=f'Votre litige concernant "{dispute.transaction.post.title}" a été résolu. Un remboursement de {dispute.refund_amount or dispute.disputed_amount}€ a été effectué.',
                dispute=dispute,
                transaction=dispute.transaction
            )
            
            # Notification pour le vendeur
            Notification.objects.create(
                user=dispute.transaction.seller,
                type='dispute_resolved',
                title='Litige résolu',
                content=f'Le litige concernant "{dispute.transaction.post.title}" a été résolu en faveur de l\'acheteur. Aucun paiement ne sera effectué.',
                dispute=dispute,
                transaction=dispute.transaction
            )
            
        elif resolution_type == 'payout':
            # Notification pour le vendeur (payout)
            seller_amount = float(dispute.disputed_amount) * 0.90
            Notification.objects.create(
                user=dispute.transaction.seller,
                type='dispute_resolved',
                title='Litige résolu en votre faveur',
                content=f'Votre litige concernant "{dispute.transaction.post.title}" a été résolu. Un paiement de {seller_amount}€ a été effectué.',
                dispute=dispute,
                transaction=dispute.transaction
            )
            
            # Notification pour l'acheteur
            Notification.objects.create(
                user=dispute.transaction.buyer,
                type='dispute_resolved',
                title='Litige résolu',
                content=f'Le litige concernant "{dispute.transaction.post.title}" a été résolu en faveur du vendeur. Aucun remboursement ne sera effectué.',
                dispute=dispute,
                transaction=dispute.transaction
            )
            
        logger.info(f"Notifications créées pour la résolution du litige {dispute.id} ({resolution_type})")
        
    except Exception as e:
        logger.error(f"Erreur lors de la création des notifications de résolution: {e}")

def create_dispute_notification(dispute):
    """
    Créer des notifications lors de la création d'un litige
    """
    try:
        # Notification pour l'acheteur (créateur du litige)
        Notification.objects.create(
            user=dispute.transaction.buyer,
            type='dispute_created',
            title='Litige créé',
            content=f'Votre litige concernant "{dispute.transaction.post.title}" a été créé et sera examiné par notre équipe.',
            dispute=dispute,
            transaction=dispute.transaction
        )
        
        # Notification pour le vendeur
        Notification.objects.create(
            user=dispute.transaction.seller,
            type='dispute_created',
            title='Litige signalé',
            content=f'Un litige a été créé concernant votre vente "{dispute.transaction.post.title}". Notre équipe va examiner la situation.',
            dispute=dispute,
            transaction=dispute.transaction
        )
        
        logger.info(f"Notifications créées pour le nouveau litige {dispute.id}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la création des notifications de litige: {e}")

def create_dispute_message_notification(dispute_message):
    """
    Créer des notifications pour les nouveaux messages de litige (non internes)
    """
    try:
        if not dispute_message.is_internal:
            # Notifier les parties impliquées (sauf l'expéditeur)
            users_to_notify = [
                dispute_message.dispute.transaction.buyer,
                dispute_message.dispute.transaction.seller
            ]
            
            for user in users_to_notify:
                if user != dispute_message.sender:
                    Notification.objects.create(
                        user=user,
                        type='dispute_message',
                        title='Nouveau message sur votre litige',
                        content=f'Un nouveau message a été ajouté à votre litige concernant "{dispute_message.dispute.transaction.post.title}".',
                        dispute=dispute_message.dispute,
                        transaction=dispute_message.dispute.transaction
                    )
            
            logger.info(f"Notifications créées pour le message de litige {dispute_message.id}")
            
    except Exception as e:
        logger.error(f"Erreur lors de la création des notifications de message: {e}")

@login_required
@require_POST
def change_currency(request):
    """
    Vue AJAX pour changer la devise préférée de l'utilisateur
    """
    try:
        data = json.loads(request.body)
        currency_code = data.get('currency')
        
        if not currency_code:
            return JsonResponse({'success': False, 'message': 'Code devise manquant'})
        
        # Vérifier que la devise est supportée
        valid_currencies = [choice[0] for choice in UserCurrency.CURRENCY_CHOICES]
        if currency_code not in valid_currencies:
            return JsonResponse({'success': False, 'message': 'Devise non supportée'})
        
        # Créer ou mettre à jour la préférence de devise
        user_currency, created = UserCurrency.objects.get_or_create(
            user=request.user,
            defaults={'preferred_currency': currency_code}
        )
        
        if not created:
            user_currency.preferred_currency = currency_code
            user_currency.save()
        
        # Récupérer le symbole de la devise
        from blizzgame.currency_service import CurrencyService
        currency_symbol = CurrencyService.CURRENCY_SYMBOLS.get(currency_code, currency_code)
        
        return JsonResponse({
            'success': True, 
            'message': f'Devise changée vers {currency_code}',
            'currency': currency_code,
            'currency_symbol': currency_symbol
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Données JSON invalides'})
    except Exception as e:
        logger.error(f"Erreur lors du changement de devise: {e}")
        return JsonResponse({'success': False, 'message': 'Erreur serveur'})

@login_required
def get_active_chats(request):
    """
    Vue pour récupérer les chats actifs pour le chat flottant
    """
    try:
        # Récupérer les transactions actives de l'utilisateur
        active_transactions = Transaction.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user),
            status__in=['pending', 'processing', 'completed']
        ).select_related('buyer', 'seller', 'post').order_by('-created_at')[:10]
        
        chats = []
        for transaction in active_transactions:
            # Déterminer l'autre utilisateur
            other_user = transaction.seller if transaction.buyer == request.user else transaction.buyer
            
            # Récupérer le dernier message
            last_message = Message.objects.filter(
                chat__transaction=transaction
            ).order_by('-created_at').first()
            
            chat_data = {
                'id': str(transaction.id),
                'other_user': {
                    'username': other_user.username,
                    'id': other_user.id
                },
                'product_title': transaction.post.title,
                'last_message': {
                    'content': last_message.content if last_message else 'Aucun message',
                    'timestamp': last_message.created_at.isoformat() if last_message else transaction.created_at.isoformat(),
                    'sender': last_message.sender.username if last_message else 'Système'
                },
                'unread_count': 0,  # TODO: Implémenter le comptage des messages non lus
                'status': transaction.status
            }
            chats.append(chat_data)
        
        return JsonResponse({
            'success': True,
            'chats': chats
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des chats actifs: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la récupération des chats'
        })

@login_required
@require_POST
def submit_report(request):
    """
    Vue pour soumettre un signalement
    """
    try:
        data = json.loads(request.body)
        print(f"Données reçues: {data}")  # Debug
        
        report_type = data.get('report_type')
        reason = data.get('reason')
        description = data.get('description')
        
        print(f"report_type: {report_type}, reason: {reason}, description: {description}")  # Debug
        
        if not all([report_type, reason]):
            return JsonResponse({'success': False, 'error': 'Données manquantes'})
        
        # Créer le signalement selon le type
        report_data = {
            'reporter': request.user,
            'report_type': report_type,
            'reason': reason,
            'description': description,
        }
        
        if report_type == 'highlight':
            highlight_id = data.get('content_id')  # Changé de 'highlight_id' à 'content_id'
            if not highlight_id:
                return JsonResponse({'success': False, 'error': 'ID du highlight manquant'})
            
            highlight = get_object_or_404(Highlight, id=highlight_id)
            # Protection contre l'auto-signalement
            if highlight.author == request.user:
                return JsonResponse({'success': False, 'error': 'Vous ne pouvez pas signaler votre propre contenu'})
            
            report_data['reported_user'] = highlight.author
            report_data['highlight'] = highlight
            
        elif report_type == 'profile':
            user_id = data.get('content_id')
            if not user_id:
                return JsonResponse({'success': False, 'error': 'ID de l\'utilisateur manquant'})
            
            reported_user = get_object_or_404(User, id=user_id)
            # Protection contre l'auto-signalement
            if reported_user == request.user:
                return JsonResponse({'success': False, 'error': 'Vous ne pouvez pas signaler votre propre profil'})
            
            report_data['reported_user'] = reported_user
            
        elif report_type == 'gaming_post':
            post_id = data.get('content_id')  # Uniformisé avec les autres types
            if not post_id:
                return JsonResponse({'success': False, 'error': 'ID du post manquant'})
            
            post = get_object_or_404(Post, id=post_id)
            # Protection contre l'auto-signalement
            if post.author == request.user:
                return JsonResponse({'success': False, 'error': 'Vous ne pouvez pas signaler votre propre contenu'})
            
            report_data['reported_user'] = post.author
            report_data['gaming_post'] = post
            
        elif report_type == 'chat_message':
            message_id = data.get('message_id')
            if not message_id:
                return JsonResponse({'success': False, 'error': 'ID du message manquant'})
            
            message = get_object_or_404(Message, id=message_id)
            report_data['reported_user'] = message.sender
            report_data['chat_message'] = message
        
        # Vérifier si l'utilisateur n'a pas déjà signalé ce contenu
        if report_type == 'highlight':
            existing_report = Report.objects.filter(
                reporter=request.user,
                highlight=report_data.get('highlight')
            ).first()
        elif report_type == 'gaming_post':
            existing_report = Report.objects.filter(
                reporter=request.user,
                gaming_post=report_data.get('gaming_post')
            ).first()
        elif report_type == 'chat_message':
            existing_report = Report.objects.filter(
                reporter=request.user,
                chat_message=report_data.get('chat_message')
            ).first()
        else:
            existing_report = None
        
        if existing_report:
            return JsonResponse({'success': False, 'error': 'Vous avez déjà signalé ce contenu'})
        
        # Créer le signalement
        report = Report.objects.create(**report_data)
        
        # Créer une notification pour les admins
        admin_users = User.objects.filter(is_staff=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                type='new_report',
                title='Nouveau signalement',
                content=f'Un nouveau signalement a été soumis par {request.user.username}',
                report=report
            )
        
        return JsonResponse({'success': True, 'message': 'Signalement envoyé avec succès'})
        
    except json.JSONDecodeError:
        print(f"Erreur dans submit_report: JSONDecodeError")  # Debug
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        print(f"Erreur dans submit_report: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()  # Debug
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def admin_reports_dashboard(request):
    """
    Dashboard admin pour gérer les signalements
    """
    try:
        # Filtres
        report_type = request.GET.get('report_type', '')
        status = request.GET.get('status', '')
        reason = request.GET.get('reason', '')
        
        # Query de base
        reports = Report.objects.select_related('reporter', 'reported_user', 'admin_reviewer').order_by('-created_at')
        
        # Application des filtres
        if report_type:
            reports = reports.filter(report_type=report_type)
        if status:
            reports = reports.filter(status=status)
        if reason:
            reports = reports.filter(reason=reason)
        
        # Statistiques
        stats = {
            'pending': Report.objects.filter(status='pending').count(),
            'under_review': Report.objects.filter(status='under_review').count(),
            'resolved': Report.objects.filter(status='resolved').count(),
            'total': Report.objects.count(),
        }
        
        context = {
            'reports': reports[:50],  # Limiter à 50 pour la performance
            'stats': stats,
        }
        
        return render(request, 'admin/reports_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans admin_reports_dashboard: {e}")
        messages.error(request, "Erreur lors du chargement des signalements")
        return redirect('admin:index')

@staff_member_required
@require_POST
def admin_send_warning(request):
    """
    Envoyer un avertissement à un utilisateur
    """
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
        warning_type = data.get('warning_type')
        reason = data.get('reason')
        
        if not all([report_id, warning_type, reason]):
            return JsonResponse({'success': False, 'error': 'Données manquantes'})
        
        report = get_object_or_404(Report, id=report_id)
        
        # Créer l'avertissement
        warning = UserWarning.objects.create(
            user=report.reported_user,
            admin=request.user,
            warning_type=warning_type,
            reason=reason,
            related_report=report
        )
        
        # Mettre à jour le signalement
        report.status = 'resolved'
        report.admin_reviewer = request.user
        report.action_taken = 'warning'
        report.admin_notes = f"Avertissement envoyé: {reason}"
        report.reviewed_at = timezone.now()
        report.save()
        
        # Créer une notification pour l'utilisateur
        Notification.objects.create(
            user=report.reported_user,
            type='warning',
            title='Avertissement reçu',
            content=f'Vous avez reçu un avertissement: {reason}',
            warning=warning
        )
        
        return JsonResponse({'success': True, 'message': 'Avertissement envoyé avec succès'})
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi d'avertissement: {e}")
        return JsonResponse({'success': False, 'error': 'Erreur serveur'})

@staff_member_required
@require_POST
def admin_ban_user(request):
    """
    Bannir un utilisateur
    """
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
        ban_type = data.get('ban_type')
        duration = data.get('duration')
        reason = data.get('reason')
        
        if not all([report_id, ban_type, reason]):
            return JsonResponse({'success': False, 'error': 'Données manquantes'})
        
        report = get_object_or_404(Report, id=report_id)
        
        # Calculer la date de fin pour bannissement temporaire
        end_date = None
        if ban_type == 'temporary' and duration:
            end_date = timezone.now() + timezone.timedelta(days=int(duration))
        
        # Créer le bannissement
        ban = UserBan.objects.create(
            user=report.reported_user,
            admin=request.user,
            ban_type=ban_type,
            reason=reason,
            end_date=end_date,
            related_report=report
        )
        
        # Mettre à jour le signalement
        report.status = 'resolved'
        report.admin_reviewer = request.user
        report.action_taken = f'{ban_type}_ban'
        report.admin_notes = f"Bannissement {ban_type}: {reason}"
        report.reviewed_at = timezone.now()
        report.save()
        
        # Créer une notification pour l'utilisateur
        ban_message = f"Bannissement {ban.get_ban_type_display().lower()}"
        if end_date:
            ban_message += f" jusqu'au {end_date.strftime('%d/%m/%Y')}"
        
        Notification.objects.create(
            user=report.reported_user,
            type='ban',
            title='Compte banni',
            content=f'{ban_message}: {reason}',
            ban=ban
        )
        
        return JsonResponse({'success': True, 'message': 'Utilisateur banni avec succès'})
        
    except Exception as e:
        logger.error(f"Erreur lors du bannissement: {e}")
        return JsonResponse({'success': False, 'error': 'Erreur serveur'})

@staff_member_required
@require_POST
def admin_dismiss_report(request):
    """
    Rejeter un signalement
    """
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
        
        if not report_id:
            return JsonResponse({'success': False, 'error': 'ID du signalement manquant'})
        
        report = get_object_or_404(Report, id=report_id)
        
        # Mettre à jour le signalement
        report.status = 'dismissed'
        report.admin_reviewer = request.user
        report.action_taken = 'none'
        report.admin_notes = "Signalement rejeté par l'admin"
        report.reviewed_at = timezone.now()
        report.save()
        
        return JsonResponse({'success': True, 'message': 'Signalement rejeté'})
        
    except Exception as e:
        logger.error(f"Erreur lors du rejet du signalement: {e}")
        return JsonResponse({'success': False, 'error': 'Erreur serveur'})

@staff_member_required
def admin_report_details(request, report_id):
    """
    Récupérer les détails d'un signalement
    """
    try:
        report = get_object_or_404(Report, id=report_id)
        
        # Vérifier si le highlight est expiré et rejeter automatiquement le signalement
        if report.highlight and report.highlight.is_expired:
            report.status = 'dismissed'
            report.admin_notes = 'Signalement automatiquement rejeté - Highlight expiré'
            report.save()
            
            return JsonResponse({
                'success': False, 
                'error': 'Ce highlight a expiré. Le signalement a été automatiquement rejeté.'
            })
        
        # Construire l'URL du contenu selon le type
        content_url = None
        if report.highlight:
            content_url = f"/highlights/for-you/?highlight={report.highlight.id}#highlight-{report.highlight.id}"
        elif report.gaming_post:
            content_url = f"/product/{report.gaming_post.id}/"
        elif report.chat_message:
            content_url = f"/chat/private/{report.chat_message.chat.id}/"
        elif report.reported_user and report.report_type == 'profile':
            content_url = f"/profile/{report.reported_user.username}/"
        
        data = {
            'success': True,
            'report': {
                'reporter': report.reporter.username,
                'reported_user': report.reported_user.username,
                'report_type': report.get_report_type_display(),
                'reason': report.get_reason_display(),
                'description': report.description,
                'created_at': report.created_at.strftime('%d/%m/%Y %H:%M'),
                'content_url': content_url,
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des détails: {e}")
        return JsonResponse({'success': False, 'error': 'Erreur serveur'})

# ===== VUES DE VÉRIFICATION EMAIL =====

def verify_email(request, token):
    """Vue pour vérifier l'email avec le token"""
    try:
        email_verification = EmailVerification.objects.get(token=token)
        
        if email_verification.is_expired:
            messages.error(request, 'Ce lien de vérification a expiré. Veuillez demander un nouveau lien.')
            return redirect('signin')
        
        if email_verification.is_verified:
            messages.info(request, 'Votre email a déjà été vérifié.')
            return redirect('signin')
        
        # Marquer comme vérifié
        email_verification.is_verified = True
        email_verification.verified_at = timezone.now()
        email_verification.save()
        
        messages.success(request, '🎉 Votre email a été vérifié avec succès ! Vous pouvez maintenant vous connecter.')
        return redirect('signin')
        
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Lien de vérification invalide.')
        return redirect('signin')

@login_required
def resend_verification_email(request):
    """Vue pour renvoyer un email de vérification avec contrôle de délai"""
    if request.method == 'POST':
        try:
            email_verification = EmailVerification.objects.get(user=request.user)
            
            # Vérifier si l'utilisateur peut renvoyer un email
            if not email_verification.can_resend_email:
                remaining_time = email_verification.time_until_next_resend
                if remaining_time:
                    minutes = int(remaining_time.total_seconds() // 60)
                    seconds = int(remaining_time.total_seconds() % 60)
                    return JsonResponse({
                        'success': False, 
                        'message': f'Veuillez attendre {minutes}m {seconds}s avant de renvoyer un email.',
                        'cooldown': True,
                        'remaining_seconds': int(remaining_time.total_seconds())
                    })
            
            if email_verification.send_verification_email():
                return JsonResponse({'success': True, 'message': 'Email de vérification envoyé !'})
            else:
                return JsonResponse({'success': False, 'message': 'Erreur lors de l\'envoi de l\'email.'})
        except EmailVerification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Aucune vérification email trouvée.'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@login_required
def send_verification_email_on_signup(request):
    """Vue pour renvoyer un email de vérification après inscription"""
    if request.method == 'POST':
        try:
            # Créer l'objet de vérification
            verification = EmailVerification.objects.create(user=request.user)
            
            # Envoyer l'email
            if verification.send_verification_email():
                messages.success(request, '📧 Email de vérification envoyé ! Vérifiez votre boîte de réception pour activer votre compte.')
                return JsonResponse({'success': True})
            else:
                messages.error(request, '❌ Erreur lors de l\'envoi de l\'email. Vérifiez la configuration email.')
                return JsonResponse({'success': False, 'error': 'Erreur d\'envoi email'})
                
        except Exception as e:
            messages.error(request, f'❌ Erreur: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def verify_email_code(request):
    """Vue pour vérifier l'email avec un code à 6 chiffres"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            verification_code = data.get('verification_code', '').strip()
            
            if not verification_code or len(verification_code) != 6 or not verification_code.isdigit():
                return JsonResponse({
                    'success': False, 
                    'message': 'Code de vérification invalide. Veuillez entrer un code à 6 chiffres.'
                })
            
            # Chercher la vérification email de l'utilisateur
            try:
                email_verification = EmailVerification.objects.get(user=request.user)
            except EmailVerification.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'message': 'Aucune vérification email trouvée. Veuillez demander un nouveau code.'
                })
            
            # Vérifier si déjà vérifié
            if email_verification.is_verified:
                return JsonResponse({
                    'success': False, 
                    'message': 'Votre email est déjà vérifié.'
                })
            
            # Vérifier si le code correspond
            if email_verification.verification_code != verification_code:
                return JsonResponse({
                    'success': False, 
                    'message': 'Code de vérification incorrect. Vérifiez votre email et réessayez.'
                })
            
            # Vérifier si le code n'est pas expiré
            if email_verification.is_expired:
                return JsonResponse({
                    'success': False, 
                    'message': 'Le code de vérification a expiré. Veuillez demander un nouveau code.'
                })
            
            # Marquer comme vérifié
            from django.utils import timezone
            email_verification.is_verified = True
            email_verification.verified_at = timezone.now()
            email_verification.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Email vérifié avec succès ! Votre compte est maintenant activé.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'message': 'Données invalides.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Erreur lors de la vérification: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})


# ===== VUES POUR LA RÉINITIALISATION DE MOT DE PASSE =====

def forgot_password(request):
    """Vue pour la demande de réinitialisation de mot de passe"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Veuillez entrer votre adresse email.')
            return render(request, 'forgot_password.html')
        
        try:
            # Vérifier si l'utilisateur existe
            print(f"[DEBUG] Recherche de l'utilisateur avec email: {email}")
            user = User.objects.get(email=email)
            print(f"[DEBUG] Utilisateur trouvé: {user.username}")
            
            # Créer un token de réinitialisation
            from .models import PasswordReset
            print("[DEBUG] Création du token de réinitialisation...")
            password_reset = PasswordReset.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            print(f"[DEBUG] Token créé: {password_reset.token}")
            
            # Envoyer l'email de réinitialisation
            print("[DEBUG] Tentative d'envoi de l'email...")
            email_sent = password_reset.send_reset_email(request)
            print(f"[DEBUG] Email envoyé: {email_sent}")
            
            if email_sent:
                messages.success(request, f'Un code de réinitialisation a été envoyé à {email}. Vérifiez votre boîte de réception et vos spams.')
                # Rediriger vers la page de saisie de code
                return redirect('reset_password_code', email=email)
            else:
                # Mode débogage : afficher le code directement
                messages.error(request, 'Erreur lors de l\'envoi de l\'email. Le code de réinitialisation est affiché ci-dessous.')
                return render(request, 'forgot_password_debug.html', {'reset_code': password_reset.reset_code})
            
        except User.DoesNotExist:
            print(f"[DEBUG] Utilisateur non trouvé pour l'email: {email}")
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe ou non
            messages.success(request, f'Si l\'adresse {email} est associée à un compte, un email de réinitialisation a été envoyé.')
        except Exception as e:
            print(f"[DEBUG] Erreur détaillée: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Erreur lors de la demande de réinitialisation: {e}")
            messages.error(request, 'Une erreur est survenue. Veuillez réessayer.')
        
        return render(request, 'forgot_password.html')
    
    return render(request, 'forgot_password.html')


def reset_password(request, token):
    """Vue pour la réinitialisation du mot de passe avec token"""
    try:
        from .models import PasswordReset
        password_reset = get_object_or_404(PasswordReset, token=token)
        
        # Vérifier si le token est valide
        if not password_reset.is_valid:
            if password_reset.is_expired:
                messages.error(request, 'Ce lien de réinitialisation a expiré. Veuillez faire une nouvelle demande.')
            elif password_reset.is_used:
                messages.error(request, 'Ce lien de réinitialisation a déjà été utilisé. Veuillez faire une nouvelle demande.')
            else:
                messages.error(request, 'Ce lien de réinitialisation n\'est pas valide.')
            return redirect('forgot_password')
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validation
            if not new_password or not confirm_password:
                messages.error(request, 'Veuillez remplir tous les champs.')
                return render(request, 'reset_password.html', {'token': token, 'user': password_reset.user})
            
            if new_password != confirm_password:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
                return render(request, 'reset_password.html', {'token': token, 'user': password_reset.user})
            
            # Validation de la force du mot de passe
            from .validators import BlizzPasswordValidator
            validator = BlizzPasswordValidator()
            try:
                validator.validate(new_password, password_reset.user)
            except Exception as e:
                messages.error(request, str(e))
                return render(request, 'reset_password.html', {'token': token, 'user': password_reset.user})
            
            # Mettre à jour le mot de passe
            password_reset.user.set_password(new_password)
            password_reset.user.save()
            
            # Marquer le token comme utilisé
            password_reset.mark_as_used()
            
            messages.success(request, 'Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.')
            return redirect('signin')
        
        return render(request, 'reset_password.html', {'token': token, 'user': password_reset.user})
        
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation: {e}")
        messages.error(request, 'Une erreur est survenue. Veuillez réessayer.')
        return redirect('forgot_password')


def reset_password_code(request, email):
    """Vue pour la saisie du code de réinitialisation"""
    if request.method == 'POST':
        code = request.POST.get('reset_code', '').strip()
        
        if not code:
            messages.error(request, 'Veuillez entrer le code de réinitialisation.')
            return render(request, 'reset_password_code.html', {'email': email})
        
        try:
            from .models import PasswordReset
            # Trouver le token de réinitialisation avec ce code
            password_reset = PasswordReset.objects.get(
                reset_code=code,
                user__email=email,
                is_used=False
            )
            
            # Vérifier si le code est valide
            if not password_reset.is_valid:
                if password_reset.is_expired:
                    messages.error(request, 'Ce code de réinitialisation a expiré. Veuillez faire une nouvelle demande.')
                else:
                    messages.error(request, 'Ce code de réinitialisation n\'est pas valide.')
                return redirect('forgot_password')
            
            # Rediriger vers la page de nouveau mot de passe avec le token
            return redirect('reset_password', token=password_reset.token)
            
        except PasswordReset.DoesNotExist:
            messages.error(request, 'Code de réinitialisation incorrect.')
            return render(request, 'reset_password_code.html', {'email': email})
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du code: {e}")
            messages.error(request, 'Une erreur est survenue. Veuillez réessayer.')
            return render(request, 'reset_password_code.html', {'email': email})
    
    return render(request, 'reset_password_code.html', {'email': email})

def simulate_cinetpay_payment_success(request, transaction):
    """
    Simule un paiement CinetPay réussi en mode test
    """
    try:
        # Créer une transaction CinetPay simulée
        cinetpay_transaction = CinetPayTransaction.objects.create(
            transaction=transaction,
            customer_id=str(transaction.buyer.id),
            customer_name=transaction.buyer.first_name or 'Test',
            customer_surname=transaction.buyer.last_name or 'User',
            customer_phone_number='+221701234567',  # Numéro de test
            customer_email=transaction.buyer.email,
            customer_address='Adresse de test',
            customer_city='Dakar',
            customer_country='SN',
            customer_state='DK',
            customer_zip_code='10000',
            amount=float(transaction.amount),
            currency='XOF',
            platform_commission=float(transaction.amount) * 0.1,  # 10% de commission
            seller_amount=float(transaction.amount) * 0.9,  # 90% pour le vendeur
            seller_phone_number='+221701234568',  # Numéro de test vendeur
            seller_country='SN',
            seller_operator='orange_money',
            status='payment_received',  # Paiement reçu
            cinetpay_transaction_id=f"TEST_{transaction.id}_{uuid.uuid4().hex[:8]}",
            payment_url='https://test.cinetpay.com',
            payment_token='test_token_123',
            payment_received_at=timezone.now()
        )
        
        # Mettre à jour le statut de la transaction
        transaction.status = 'processing'
        transaction.save()
        
        # Créer une notification pour le vendeur
        Notification.objects.create(
            user=transaction.seller,
            type='transaction_update',
            title='Paiement reçu',
            content=f"L'acheteur a payé {transaction.amount}€ pour {transaction.post.title}. Le chat est maintenant activé.",
            transaction=transaction
        )
        
        # Créer une notification pour l'acheteur
        Notification.objects.create(
            user=transaction.buyer,
            type='transaction_update',
            title='Paiement confirmé',
            content=f"Votre paiement de {transaction.amount}€ a été confirmé. Vous pouvez maintenant discuter avec le vendeur.",
            transaction=transaction
        )
        
        messages.success(request, '🧪 Mode test: Paiement simulé avec succès! Le chat est maintenant activé.')
        return redirect('transaction_detail', transaction_id=transaction.id)
        
    except Exception as e:
        logger.error(f"Erreur lors de la simulation du paiement: {e}")
        messages.error(request, "Erreur lors de la simulation du paiement. Veuillez réessayer.")
        return redirect('transaction_detail', transaction_id=transaction.id)


# ===== GESTION DES SANCTIONS APRÈS RÉSOLUTION DE LITIGE =====

@staff_member_required
def admin_dispute_followup(request, dispute_id):
    """
    Page de suivi après résolution d'un litige pour gérer les sanctions
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    # Déterminer qui est le perdant du litige
    if dispute.resolution == 'refund':
        # Remboursement = vendeur perd
        losing_user = dispute.transaction.seller
        winning_user = dispute.transaction.buyer
        resolution_type = 'remboursement'
    elif dispute.resolution == 'payout':
        # Payout = acheteur perd
        losing_user = dispute.transaction.buyer
        winning_user = dispute.transaction.seller
        resolution_type = 'paiement vendeur'
    else:
        # Litige non résolu ou autre
        messages.error(request, 'Ce litige n\'a pas encore été résolu.')
        return redirect('admin_dispute_detail', dispute_id=dispute.id)
    
    # Récupérer les statistiques du perdant
    from .models import UserWarning, UserBan
    
    # Compter les avertissements actifs
    active_warnings = UserWarning.objects.filter(
        user=losing_user,
        is_active=True
    ).exclude(
        expires_at__lt=timezone.now()
    ).count()
    
    # Compter les bannissements actifs
    active_bans = UserBan.objects.filter(
        user=losing_user,
        is_active=True
    ).exclude(
        ends_at__lt=timezone.now()
    ).count()
    
    # Statistiques générales
    total_disputes_as_buyer = Dispute.objects.filter(transaction__buyer=losing_user).count()
    total_disputes_as_seller = Dispute.objects.filter(transaction__seller=losing_user).count()
    
    # Litiges perdus par l'utilisateur perdant (séparément pour éviter les problèmes d'union)
    lost_as_buyer = Dispute.objects.filter(
        transaction__buyer=losing_user,
        resolution='payout'
    ).count()
    lost_as_seller = Dispute.objects.filter(
        transaction__seller=losing_user,
        resolution='refund'
    ).count()
    total_lost_disputes = lost_as_buyer + lost_as_seller
    
    # Récupérer les 10 derniers litiges perdus pour l'affichage
    lost_disputes = list(Dispute.objects.filter(
        transaction__buyer=losing_user,
        resolution='payout'
    )) + list(Dispute.objects.filter(
        transaction__seller=losing_user,
        resolution='refund'
    ))
    lost_disputes.sort(key=lambda x: x.resolved_at, reverse=True)
    lost_disputes = lost_disputes[:10]
    
    context = {
        'dispute': dispute,
        'losing_user': losing_user,
        'winning_user': winning_user,
        'resolution_type': resolution_type,
        'active_warnings': active_warnings,
        'active_bans': active_bans,
        'lost_disputes': lost_disputes[:10],  # 10 derniers litiges perdus
        'total_disputes_as_buyer': total_disputes_as_buyer,
        'total_disputes_as_seller': total_disputes_as_seller,
        'total_lost_disputes': total_lost_disputes,
    }
    
    return render(request, 'admin/dispute_followup.html', context)


@staff_member_required
@require_POST
def admin_warn_user(request, dispute_id):
    """
    Avertir l'utilisateur perdant du litige
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    # Déterminer qui est le perdant
    if dispute.resolution == 'refund':
        losing_user = dispute.transaction.seller
    elif dispute.resolution == 'payout':
        losing_user = dispute.transaction.buyer
    else:
        messages.error(request, 'Litige non résolu.')
        return redirect('admin_dispute_followup', dispute_id=dispute.id)
    
    # Récupérer les données du formulaire
    warning_type = request.POST.get('warning_type')
    severity = request.POST.get('severity')
    reason = request.POST.get('reason')
    details = request.POST.get('details', '')
    expires_days = request.POST.get('expires_days', 30)
    
    # Validation
    if not all([warning_type, severity, reason]):
        messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
        return redirect('admin_dispute_followup', dispute_id=dispute.id)
    
    try:
        from .models import UserWarning
        from datetime import timedelta
        
        # Calculer la date d'expiration
        expires_at = timezone.now() + timedelta(days=int(expires_days))
        
        # Créer l'avertissement
        warning = UserWarning.objects.create(
            user=losing_user,
            admin=request.user,
            dispute=dispute,
            warning_type=warning_type,
            severity=severity,
            reason=reason,
            details=details,
            expires_at=expires_at
        )
        
        # Gérer les annonces de l'utilisateur averti selon la sévérité
        try:
            from .post_management import deactivate_user_posts
            if severity in ['high', 'critical']:
                # Pour les avertissements graves, désactiver temporairement les annonces
                deactivated_count = deactivate_user_posts(losing_user, f"Avertissement {severity}: {reason}")
                logger.info(f"{deactivated_count} annonces désactivées pour {losing_user.username} suite à l'avertissement {severity}")
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation des annonces de {losing_user.username}: {e}")
            # Ne pas faire échouer l'avertissement si la désactivation des annonces échoue
        
        # Créer une notification pour l'utilisateur
        Notification.objects.create(
            user=losing_user,
            type='warning',
            title=f'Avertissement - {warning.get_severity_display()}',
            content=f'Vous avez reçu un avertissement suite au litige concernant "{dispute.transaction.post.title}". Raison: {reason}',
            dispute=dispute
        )
        
        messages.success(request, f'Avertissement envoyé à {losing_user.username}.')
        logger.info(f"Admin {request.user.username} a averti {losing_user.username} pour le litige {dispute.id}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'avertissement: {e}")
        messages.error(request, 'Erreur lors de l\'envoi de l\'avertissement.')
    
    return redirect('admin_dispute_followup', dispute_id=dispute.id)


@staff_member_required
@require_POST
def admin_ban_user(request, dispute_id):
    """
    Bannir l'utilisateur perdant du litige
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    # Déterminer qui est le perdant
    if dispute.resolution == 'refund':
        losing_user = dispute.transaction.seller
    elif dispute.resolution == 'payout':
        losing_user = dispute.transaction.buyer
    else:
        messages.error(request, 'Litige non résolu.')
        return redirect('admin_dispute_followup', dispute_id=dispute.id)
    
    # Récupérer les données du formulaire
    ban_type = request.POST.get('ban_type')
    reason = request.POST.get('reason')
    details = request.POST.get('details', '')  # Optionnel
    ban_days = request.POST.get('ban_days', 7)  # Par défaut 7 jours
    
    # Validation
    if not all([ban_type, reason]):
        messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
        return redirect('admin_dispute_followup', dispute_id=dispute.id)
    
    try:
        from .models import UserBan
        from datetime import timedelta
        
        # Calculer la date de fin pour les bannissements temporaires
        ends_at = None
        if ban_type == 'temporary':
            ends_at = timezone.now() + timedelta(days=int(ban_days))
        
        # Créer le bannissement
        ban = UserBan.objects.create(
            user=losing_user,
            admin=request.user,
            dispute=dispute,
            ban_type=ban_type,
            reason=reason,
            details=details,
            ends_at=ends_at
        )
        
        # Gérer les annonces de l'utilisateur banni
        try:
            from .post_management import deactivate_user_posts
            deactivated_count = deactivate_user_posts(losing_user, f"Bannissement suite au litige: {reason}")
            logger.info(f"{deactivated_count} annonces désactivées pour {losing_user.username}")
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation des annonces de {losing_user.username}: {e}")
            # Ne pas faire échouer le bannissement si la désactivation des annonces échoue
        
        # Créer une notification pour l'utilisateur
        ban_duration = f" pour {ban_days} jours" if ban_type == 'temporary' else " définitivement"
        Notification.objects.create(
            user=losing_user,
            type='ban',
            title=f'Bannissement - {ban.get_ban_type_display()}',
            content=f'Vous avez été banni{ban_duration} suite au litige concernant "{dispute.transaction.post.title}". Raison: {reason}',
            dispute=dispute
        )
        
        messages.success(request, f'Utilisateur {losing_user.username} banni avec succès.')
        logger.info(f"Admin {request.user.username} a banni {losing_user.username} pour le litige {dispute.id}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du bannissement: {e}")
        messages.error(request, 'Erreur lors du bannissement.')
    
    return redirect('admin_dispute_followup', dispute_id=dispute.id)


def banned_user_view(request):
    """
    Vue pour afficher la page d'information pour les utilisateurs bannis
    """
    # Cette vue est appelée par le middleware quand un utilisateur banni tente d'accéder
    # Les informations du bannissement sont passées via la session
    ban_info = request.session.get('ban_info', {})
    
    context = {
        'ban_reason': ban_info.get('reason', 'Non spécifié'),
        'ban_type': ban_info.get('ban_type', 'permanent'),
        'ban_end_date': ban_info.get('ends_at', ''),
        'ban_details': ban_info.get('details', ''),
    }
    
    return render(request, 'account/banned.html', context)


@login_required
def get_unread_notifications_count(request):
    """
    API pour obtenir le nombre de notifications non lues
    """
    try:
        # Récupérer le profil utilisateur BlizzGame
        user_profile, created = User.objects.get_or_create(
            username=request.user.username,
            defaults={'email': request.user.email}
        )
        
        count = Notification.objects.filter(
            user=user_profile,
            is_read=False
        ).count()
        
        return JsonResponse({'count': count})
    except Exception as e:
        logger.error(f"Erreur lors du comptage des notifications: {e}")
        return JsonResponse({'count': 0})


@login_required
def mark_all_notifications_read(request):
    """
    Marquer toutes les notifications comme lues
    """
    try:
        # Récupérer le profil utilisateur BlizzGame
        user_profile, created = User.objects.get_or_create(
            username=request.user.username,
            defaults={'email': request.user.email}
        )
        
        # Marquer toutes les notifications non lues comme lues
        updated_count = Notification.objects.filter(
            user=user_profile,
            is_read=False
        ).update(is_read=True)
        
        messages.success(request, f'{updated_count} notifications marquées comme lues')
        
    except Exception as e:
        logger.error(f"Erreur lors du marquage des notifications: {e}")
        messages.error(request, 'Erreur lors du marquage des notifications')
    
    return redirect('notifications')


# ===== VUES POUR LES NOTIFICATIONS MARKETING =====

@login_required
def get_marketing_notification(request):
    """
    Récupère la notification marketing active pour l'utilisateur
    """
    try:
        from .marketing_utils import MarketingNotificationManager
        
        # Créer ou récupérer la notification du jour
        notification = MarketingNotificationManager.create_daily_notification(request.user)
        
        if not notification:
            return JsonResponse({'success': False, 'message': 'Aucune notification disponible'})
        
        # Préparer les données du produit
        product = notification.product
        
        # Nettoyer la description HTML
        import re
        clean_description = re.sub(r'<[^>]+>', '', product.description)  # Supprimer les balises HTML
        clean_description = re.sub(r'\s+', ' ', clean_description)  # Remplacer les espaces multiples
        clean_description = clean_description.strip()
        
        # Vérifier que le slug existe
        if not product.slug:
            logger.warning(f"Produit {product.id} n'a pas de slug, utilisation de l'ID")
            shop_url = f'/shop/product/{product.id}/'
        else:
            shop_url = f'/shop/product/{product.slug}/'
        
        product_data = {
            'id': str(notification.id),
            'product_id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image_url': product.featured_image.url if product.featured_image else None,
            'description': clean_description[:100] + '...' if len(clean_description) > 100 else clean_description,
            'shop_url': shop_url,
        }
        
        return JsonResponse({
            'success': True,
            'notification': product_data
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la notification marketing: {e}")
        return JsonResponse({'success': False, 'message': 'Erreur serveur'})


@login_required
@require_POST
def dismiss_marketing_notification(request):
    """
    Ferme une notification marketing
    """
    try:
        notification_id = request.POST.get('notification_id')
        
        if not notification_id:
            return JsonResponse({'success': False, 'message': 'ID de notification manquant'})
        
        from .marketing_utils import MarketingNotificationManager
        
        success = MarketingNotificationManager.dismiss_notification(notification_id, request.user)
        
        if success:
            return JsonResponse({'success': True, 'message': 'Notification fermée'})
        else:
            return JsonResponse({'success': False, 'message': 'Notification non trouvée'})
            
    except Exception as e:
        logger.error(f"Erreur lors de la fermeture de la notification marketing: {e}")
        return JsonResponse({'success': False, 'message': 'Erreur serveur'})


@login_required
def check_marketing_notification(request):
    """
    Vérifie si l'utilisateur a une notification marketing à afficher
    """
    try:
        from .marketing_utils import MarketingNotificationManager
        
        # Vérifier s'il y a une notification active pour aujourd'hui
        today = timezone.now().date()
        active_notification = MarketingNotification.objects.filter(
            user=request.user,
            shown_date=today,
            is_dismissed=False
        ).first()
        
        if active_notification:
            return JsonResponse({'show': True, 'notification_id': str(active_notification.id)})
        else:
            return JsonResponse({'show': False})
            
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la notification marketing: {e}")
        return JsonResponse({'show': False})


def condition_utilisation(request):
    """Page des conditions d'utilisation"""
    return render(request, 'condition_utilisation.html', {
        'page_title': 'Conditions d\'utilisation - Blizz Gaming'
    })

def politique_confidentialite(request):
    """Page de la politique de confidentialité"""
    return render(request, 'politique.html', {
        'page_title': 'Politique de confidentialité - Blizz Gaming'
    })

@csrf_exempt
def debug_transaction_status(request, transaction_id):
    """
    Vue de diagnostic pour vérifier le statut d'une transaction
    Accessible uniquement en mode DEBUG ou pour les admins
    """
    if not settings.DEBUG and not request.user.is_staff:
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        data = {
            'transaction_id': str(transaction.id),
            'status': transaction.status,
            'buyer': transaction.buyer.username,
            'seller': transaction.seller.username,
            'amount': float(transaction.amount),
            'created_at': transaction.created_at.isoformat(),
            'updated_at': transaction.updated_at.isoformat(),
            'post': {
                'id': transaction.post.id,
                'title': transaction.post.title,
                'is_on_sale': transaction.post.is_on_sale,
                'is_in_transaction': transaction.post.is_in_transaction,
                'is_sold': transaction.post.is_sold,
            },
            'cinetpay_transaction': None
        }
        
        if hasattr(transaction, 'cinetpay_transaction'):
            cinetpay = transaction.cinetpay_transaction
            data['cinetpay_transaction'] = {
                'id': cinetpay.id,
                'status': cinetpay.status,
                'amount': float(cinetpay.amount),
                'created_at': cinetpay.created_at.isoformat(),
            }
        
        return JsonResponse(data)
        
    except Transaction.DoesNotExist:
        return JsonResponse({
            'error': 'Transaction non trouvée',
            'transaction_id': transaction_id,
            'suggestions': []
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'transaction_id': transaction_id
        }, status=500)

# ===== Webhook pour nettoyage automatique =====

@csrf_exempt
@require_POST
def webhook_cleanup_transactions(request):
    """
    Endpoint webhook pour déclencher le nettoyage des transactions abandonnées.
    Utilisé par GitHub Actions pour automatiser le nettoyage quotidien.
    
    Headers requis:
        X-Webhook-Secret: clé secrète pour sécuriser l'endpoint
    
    Body JSON (optionnel):
        {
            "timeout_hours": "2"  // timeout en heures, défaut: 2
        }
    
    Réponse:
        {
            "success": true,
            "message": "Nettoyage terminé: X transactions nettoyées",
            "cleaned_count": X,
            "timestamp": "2024-09-26T12:00:00Z"
        }
    """
    try:
        # Vérifier la clé secrète
        webhook_secret = getattr(settings, 'WEBHOOK_SECRET', 'blizz-game-cleanup-2024')
        provided_secret = request.headers.get('X-Webhook-Secret', '')
        
        if not hmac.compare_digest(webhook_secret, provided_secret):
            logger.warning(f"Tentative d'accès webhook non autorisée depuis {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({
                "success": False,
                "error": "Accès non autorisé",
                "timestamp": timezone.now().isoformat()
            }, status=403)
        
        # Récupérer les paramètres
        try:
            body = json.loads(request.body.decode('utf-8')) if request.body else {}
        except json.JSONDecodeError:
            body = {}
        
        timeout_hours = int(body.get('timeout_hours', 2))
        timeout_minutes = timeout_hours * 60
        
        logger.info(f"🧹 Nettoyage des transactions déclenché via webhook (timeout: {timeout_hours}h)")
        
        # Capturer la sortie de la commande pour compter les nettoyages
        from io import StringIO
        import sys
        from django.core.management import call_command
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            call_command('cleanup_expired_transactions', 
                        timeout_minutes=timeout_minutes,
                        verbosity=1)
            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Analyser la sortie pour compter les nettoyages
        cleaned_count = 0
        cinetpay_cleaned = 0
        
        # Rechercher le nombre de transactions nettoyées
        import re
        
        # Transactions principales
        match = re.search(r'(\d+) transactions nettoyées', output)
        if match:
            cleaned_count = int(match.group(1))
        
        # Transactions CinetPay orphelines
        match = re.search(r'(\d+) transactions CinetPay orphelines annulées', output)
        if match:
            cinetpay_cleaned = int(match.group(1))
        
        total_cleaned = cleaned_count + cinetpay_cleaned
        
        # Message de résultat
        if total_cleaned > 0:
            message_parts = []
            if cleaned_count > 0:
                message_parts.append(f"{cleaned_count} transactions abandonnées")
            if cinetpay_cleaned > 0:
                message_parts.append(f"{cinetpay_cleaned} transactions CinetPay orphelines")
            
            message = f"Nettoyage terminé: {' et '.join(message_parts)} nettoyées"
        else:
            message = "Nettoyage terminé: aucune transaction à nettoyer"
        
        logger.info(f"✅ Nettoyage webhook terminé: {total_cleaned} transactions nettoyées")
        
        return JsonResponse({
            "success": True,
            "message": message,
            "cleaned_count": total_cleaned,
            "details": {
                "abandoned_transactions": cleaned_count,
                "orphaned_cinetpay": cinetpay_cleaned,
                "timeout_hours": timeout_hours
            },
            "timestamp": timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage webhook: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=500)
