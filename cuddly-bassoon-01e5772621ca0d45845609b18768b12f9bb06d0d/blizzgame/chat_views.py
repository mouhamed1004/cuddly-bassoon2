from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import uuid
import os
import logging
from .models import Transaction, Chat, Message, Dispute, DisputeMessage, Notification, Profile
from .consumers import TransactionChatConsumer, DisputeChatConsumer

logger = logging.getLogger(__name__)

@login_required
def transaction_chat(request, transaction_id):
    """
    Vue principale pour le chat de transaction entre vendeur et acheteur
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Vérifier que l'utilisateur a accès à cette transaction
    if request.user != transaction.buyer and request.user != transaction.seller:
        return redirect('home')
    
    # Vérifier si le chat est bloqué (seulement ouvert en processing)
    chat_locked = transaction.status not in ['processing']
    
    # Récupérer ou créer le chat
    chat, created = Chat.objects.get_or_create(
        transaction=transaction,
        defaults={
            'is_active': True,
            'is_locked': chat_locked
        }
    )
    
    # Mettre à jour le statut de blocage si le chat existe déjà
    if not created:
        chat.is_locked = chat_locked
        chat.save()
    
    # Récupérer les messages
    chat_messages = Message.objects.filter(chat=chat).order_by('created_at')
    
    # Marquer les messages comme lus
    Message.objects.filter(chat=chat, is_read=False).exclude(sender=request.user).update(is_read=True)
    
    context = {
        'transaction': transaction,
        'chat': chat,
        'chat_messages': chat_messages,
        'chat_locked': chat_locked,
        'other_user': transaction.seller if request.user == transaction.buyer else transaction.buyer,
        'websocket_url': f'ws://{request.get_host()}/ws/chat/transaction/{transaction_id}/'
    }
    
    return render(request, 'chat/transaction_chat.html', context)

@login_required
def dispute_chat(request, dispute_id):
    """
    Vue pour le chat de litige (admin + vendeur + acheteur)
    """
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    # Vérifier que l'utilisateur a accès à ce litige
    if not (request.user == dispute.transaction.buyer or 
            request.user == dispute.transaction.seller or 
            request.user.is_staff):
        return redirect('home')
    
    # Récupérer ou créer le chat de litige
    chat, created = Chat.objects.get_or_create(
        dispute=dispute,
        defaults={
            'is_active': True,
            'is_locked': False
        }
    )
    
    # Récupérer les messages
    chat_messages = Message.objects.filter(chat=chat).order_by('created_at')
    
    # Marquer les messages comme lus
    Message.objects.filter(chat=chat, is_read=False).exclude(sender=request.user).update(is_read=True)
    
    context = {
        'dispute': dispute,
        'chat': chat,
        'chat_messages': chat_messages,
        'transaction': dispute.transaction,
        'is_admin': request.user.is_staff,
        'websocket_url': f'ws://{request.get_host()}/ws/chat/dispute/{dispute_id}/'
    }
    
    return render(request, 'chat/dispute_chat.html', context)

@login_required
@require_http_methods(["POST"])
def send_message(request, chat_id):
    """
    API pour envoyer un message dans un chat
    """
    try:
        # Log pour déboguer
        logger.info(f"[CHAT DEBUG] Tentative d'envoi de message - User: {request.user.username}, Chat ID: {chat_id}")
        
        # Gérer les données form-data et JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            message_type = data.get('message_type', 'text')
        else:
            # Données form-data
            content = request.POST.get('content', '').strip()
            message_type = request.POST.get('message_type', 'text')
        
        if not content:
            return JsonResponse({'error': 'Le contenu du message ne peut pas être vide'}, status=400)
        
        try:
            chat = get_object_or_404(Chat, id=chat_id)
            logger.info(f"[CHAT DEBUG] Chat trouvé - ID: {chat.id}")
        except Exception as e:
            logger.error(f"[CHAT DEBUG] Erreur lors de la récupération du chat: {e}")
            return JsonResponse({'error': 'Chat introuvable'}, status=404)
        
        # Log détaillé pour déboguer l'accès
        logger.info(f"[CHAT DEBUG] Transaction: {chat.transaction.id if chat.transaction else 'None'}")
        logger.info(f"[CHAT DEBUG] Dispute: {chat.dispute.id if chat.dispute else 'None'}")
        
        if chat.transaction:
            logger.info(f"[CHAT DEBUG] Buyer: {chat.transaction.buyer.username} (ID: {chat.transaction.buyer.id})")
            logger.info(f"[CHAT DEBUG] Seller: {chat.transaction.seller.username} (ID: {chat.transaction.seller.id})")
            logger.info(f"[CHAT DEBUG] User actuel: {request.user.username} (ID: {request.user.id})")
            logger.info(f"[CHAT DEBUG] Buyer == User: {request.user == chat.transaction.buyer}")
            logger.info(f"[CHAT DEBUG] Seller == User: {request.user == chat.transaction.seller}")
        
        # Test has_access
        has_access_result = chat.has_access(request.user)
        logger.info(f"[CHAT DEBUG] has_access result: {has_access_result}")
        
        # Vérifier que l'utilisateur a accès à ce chat
        if not has_access_result:
            logger.error(f"[CHAT DEBUG] Accès refusé pour {request.user.username}")
            return JsonResponse({'error': 'Accès refusé'}, status=403)
        
        # Vérifier si le chat est bloqué
        if chat.is_locked and not request.user.is_staff:
            return JsonResponse({'error': 'Le chat est bloqué'}, status=403)
        
        # Créer le message
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=content,
            message_type=message_type
        )
        
        # Créer une notification pour l'autre utilisateur
        other_user = chat.get_other_user(request.user)
        if other_user:
            from .models import Notification
            Notification.objects.create(
                user=other_user,
                type='new_message',
                title='Nouveau message',
                content=f"Nouveau message de {request.user.username} dans la transaction",
                transaction=chat.transaction if chat.transaction else None,
                dispute=chat.dispute if chat.dispute else None
            )
        
        # Envoyer via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        group_name = f'chat_{chat.id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'sender': message.sender.username,
                    'sender_id': message.sender.id,
                    'created_at': message.created_at.isoformat(),
                    'message_type': message.message_type,
                    'is_read': message.is_read
                }
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message_id': str(message.id),
            'created_at': message.created_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def upload_chat_image(request, chat_id):
    """
    API pour uploader une image dans un chat
    """
    try:
        chat = get_object_or_404(Chat, id=chat_id)
        
        # Vérifier que l'utilisateur a accès à ce chat
        if not chat.has_access(request.user):
            return JsonResponse({'error': 'Accès refusé'}, status=403)
        
        # Vérifier si le chat est bloqué
        if chat.is_locked and not request.user.is_staff:
            return JsonResponse({'error': 'Le chat est bloqué'}, status=403)
        
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'Aucune image fournie'}, status=400)
        
        image = request.FILES['image']
        
        # Vérifier la taille de l'image (max 5MB)
        if image.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'L\'image est trop volumineuse (max 5MB)'}, status=400)
        
        # Vérifier le type de fichier
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image.content_type not in allowed_types:
            return JsonResponse({'error': 'Type de fichier non supporté'}, status=400)
        
        # Sauvegarder l'image
        filename = f'chat_images/{uuid.uuid4()}_{image.name}'
        file_path = default_storage.save(filename, ContentFile(image.read()))
        
        # Créer le message avec l'image
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=f'Image: {image.name}',
            message_type='image',
            image=file_path
        )
        
        # Créer une notification pour les autres utilisateurs
        other_users = chat.get_other_users(request.user)
        for user in other_users:
            Notification.objects.create(
                user=user,
                title='Nouvelle image',
                message=f'{request.user.username} a partagé une image',
                notification_type='message',
                related_object_id=chat.id
            )
        
        # Envoyer via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        group_name = f'chat_{chat.id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'sender': message.sender.username,
                    'sender_id': message.sender.id,
                    'created_at': message.created_at.isoformat(),
                    'message_type': message.message_type,
                    'image_url': message.image.url if message.image else None,
                    'is_read': message.is_read
                }
            }
        )
        
        return JsonResponse({
            'success': True,
            'message_id': str(message.id),
            'image_url': message.image.url if message.image else None,
            'created_at': message.created_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def mark_messages_read(request, chat_id):
    """
    API pour marquer les messages comme lus
    """
    try:
        chat = get_object_or_404(Chat, id=chat_id)
        
        # Vérifier que l'utilisateur a accès à ce chat
        if not chat.has_access(request.user):
            return JsonResponse({'error': 'Accès refusé'}, status=403)
        
        # Marquer les messages comme lus
        Message.objects.filter(chat=chat, is_read=False).exclude(sender=request.user).update(is_read=True)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chat_list(request):
    """
    Vue pour lister tous les chats de l'utilisateur
    """
    # Récupérer tous les chats de l'utilisateur
    user_chats = Chat.objects.filter(
        models.Q(transaction__buyer=request.user) |
        models.Q(transaction__seller=request.user) |
        models.Q(dispute__transaction__buyer=request.user) |
        models.Q(dispute__transaction__seller=request.user)
    ).distinct().order_by('-updated_at')
    
    # Ajouter des informations supplémentaires pour chaque chat
    chat_data = []
    for chat in user_chats:
        last_message = chat.messages.last()
        unread_count = chat.messages.filter(is_read=False).exclude(sender=request.user).count()
        
        chat_data.append({
            'chat': chat,
            'last_message': last_message,
            'unread_count': unread_count,
            'other_user': chat.get_other_user(request.user)
        })
    
    context = {
        'chats': chat_data
    }
    
    return render(request, 'chat/chat_list.html', context)

