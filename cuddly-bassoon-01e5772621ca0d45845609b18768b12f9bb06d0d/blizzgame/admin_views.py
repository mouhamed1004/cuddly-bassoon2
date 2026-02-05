"""
Vues admin personnalisées pour la gestion des payouts et notifications
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from datetime import datetime, timedelta
import csv
import json

from .models import PayoutRequest, EscrowTransaction, Transaction, Chat, Message, PendingEmailNotification

@staff_member_required
def payout_dashboard(request):
    """
    Tableau de bord pour la gestion des payouts
    """
    # Statistiques générales
    total_payouts = PayoutRequest.objects.count()
    pending_payouts = PayoutRequest.objects.filter(status='pending').count()
    processing_payouts = PayoutRequest.objects.filter(status='processing').count()
    completed_payouts = PayoutRequest.objects.filter(status='completed').count()
    failed_payouts = PayoutRequest.objects.filter(status='failed').count()
    
    # Montants
    total_amount_eur = PayoutRequest.objects.filter(currency='EUR').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_amount_xof = PayoutRequest.objects.filter(currency='XOF').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Conversion EUR vers XOF (approximatif)
    if total_amount_eur > 0:
        total_amount_xof += float(total_amount_eur) * 655.957
    
    # Payouts récents (7 derniers jours)
    week_ago = timezone.now() - timedelta(days=7)
    recent_payouts = PayoutRequest.objects.filter(created_at__gte=week_ago).count()
    
    # Payouts par type
    seller_payouts = PayoutRequest.objects.filter(payout_type='seller_payout').count()
    buyer_refunds = PayoutRequest.objects.filter(payout_type='buyer_refund').count()
    
    # Payouts en attente par opérateur
    pending_by_operator = PayoutRequest.objects.filter(status='pending').values(
        'recipient_operator'
    ).annotate(count=Count('id')).order_by('-count')
    
    # Payouts en attente par pays
    pending_by_country = PayoutRequest.objects.filter(status='pending').values(
        'recipient_country'
    ).annotate(count=Count('id')).order_by('-count')
    
    context = {
        'total_payouts': total_payouts,
        'pending_payouts': pending_payouts,
        'processing_payouts': processing_payouts,
        'completed_payouts': completed_payouts,
        'failed_payouts': failed_payouts,
        'total_amount_eur': total_amount_eur,
        'total_amount_xof': total_amount_xof,
        'recent_payouts': recent_payouts,
        'seller_payouts': seller_payouts,
        'buyer_refunds': buyer_refunds,
        'pending_by_operator': pending_by_operator,
        'pending_by_country': pending_by_country,
    }
    
    return render(request, 'admin/payout_dashboard.html', context)

@staff_member_required
def payout_list(request):
    """
    Liste des payouts avec filtres et actions en masse
    """
    # Filtres
    status_filter = request.GET.get('status', '')
    operator_filter = request.GET.get('operator', '')
    country_filter = request.GET.get('country', '')
    search_query = request.GET.get('search', '')
    
    # Construction de la requête avec optimisation (select_related pour éviter N+1 queries)
    payouts = PayoutRequest.objects.select_related(
        'escrow_transaction',
        'escrow_transaction__cinetpay_transaction',
        'escrow_transaction__cinetpay_transaction__transaction',
        'escrow_transaction__cinetpay_transaction__transaction__seller',
        'escrow_transaction__cinetpay_transaction__transaction__seller__payment_info',
        'escrow_transaction__cinetpay_transaction__transaction__dispute',
        'escrow_transaction__cinetpay_transaction__transaction__dispute__chat',
    ).all()
    
    if status_filter:
        payouts = payouts.filter(status=status_filter)
    
    if operator_filter:
        payouts = payouts.filter(recipient_operator=operator_filter)
    
    if country_filter:
        payouts = payouts.filter(recipient_country=country_filter)
    
    if search_query:
        payouts = payouts.filter(
            Q(recipient_phone__icontains=search_query) |
            Q(cinetpay_payout_id__icontains=search_query) |
            Q(escrow_transaction__cinetpay_transaction__transaction__seller__username__icontains=search_query)
        )
    
    # Tri
    payouts = payouts.order_by('-created_at')
    
    # Pagination (optionnel)
    from django.core.paginator import Paginator
    paginator = Paginator(payouts, 50)  # 50 payouts par page
    page_number = request.GET.get('page')
    payouts_page = paginator.get_page(page_number)
    
    # Calculer le montant total en XOF
    from decimal import Decimal
    total_amount_eur = sum(payout.amount for payout in payouts if payout.currency == 'EUR')
    total_amount_xof = total_amount_eur * Decimal('655.957')
    
    # Options pour les filtres
    status_choices = PayoutRequest.STATUS_CHOICES
    operator_choices = PayoutRequest.objects.values_list('recipient_operator', flat=True).distinct()
    country_choices = PayoutRequest.objects.values_list('recipient_country', flat=True).distinct()
    
    context = {
        'payouts': payouts_page,
        'total_amount_xof': total_amount_xof,
        'status_choices': status_choices,
        'operator_choices': operator_choices,
        'country_choices': country_choices,
        'current_filters': {
            'status': status_filter,
            'operator': operator_filter,
            'country': country_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'admin/payout_list.html', context)

@staff_member_required
def export_payouts_csv(request):
    """
    Export des payouts en CSV pour CinetPay
    """
    # Récupérer les payouts en attente
    payouts = PayoutRequest.objects.filter(status='pending').order_by('created_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payouts_cinetpay.csv"'
    
    writer = csv.writer(response)
    
    # En-têtes pour CinetPay
    writer.writerow([
        'ID', 'Vendeur', 'Email', 'Montant (XOF)', 'Téléphone', 
        'Pays', 'Opérateur', 'Description', 'Date'
    ])
    
    for payout in payouts:
        try:
            seller = payout.escrow_transaction.cinetpay_transaction.transaction.seller
            seller_email = seller.email
            seller_username = seller.username
            transaction = payout.escrow_transaction.cinetpay_transaction.transaction
            description = f"Payout {transaction.post.title[:30]}"
        except:
            seller_email = "N/A"
            seller_username = "N/A"
            description = f"Payout {payout.id}"
        
        # Convertir EUR en XOF
        amount_xof = float(payout.amount) * 655.957 if payout.currency == 'EUR' else float(payout.amount)
        
        writer.writerow([
            str(payout.id)[:8],
            seller_username,
            seller_email,
            f"{amount_xof:.0f}",
            payout.recipient_phone,
            payout.recipient_country,
            payout.recipient_operator,
            description,
            payout.created_at.strftime('%d/%m/%Y')
        ])
    
    return response

@staff_member_required
def payout_stats_api(request):
    """
    API pour les statistiques des payouts (AJAX)
    """
    # Statistiques par jour (30 derniers jours)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    daily_stats = []
    for i in range(30):
        date = timezone.now() - timedelta(days=i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = PayoutRequest.objects.filter(
            created_at__range=[start_of_day, end_of_day]
        ).count()
        
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Statistiques par opérateur
    operator_stats = PayoutRequest.objects.values('recipient_operator').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return JsonResponse({
        'daily_stats': daily_stats,
        'operator_stats': list(operator_stats)
    })

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def update_payout_status(request, payout_id):
    """
    Met à jour le statut d'un payout via AJAX
    """
    try:
        # Récupérer le payout
        payout = get_object_or_404(PayoutRequest, id=payout_id)
        
        # Parser les données JSON
        data = json.loads(request.body)
        new_status = data.get('status')
        
        # Valider le statut
        valid_statuses = ['pending', 'processing', 'completed', 'failed']
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Statut invalide. Statuts valides: {", ".join(valid_statuses)}'
            })
        
        # Sauvegarder l'ancien statut pour les logs
        old_status = payout.status
        
        # Mettre à jour le statut
        payout.status = new_status
        
        # Mettre à jour completed_at si le statut devient 'completed'
        if new_status == 'completed' and not payout.completed_at:
            payout.completed_at = timezone.now()
        elif new_status != 'completed':
            payout.completed_at = None
        
        payout.save()
        
        # Log de l'action
        print(f"[PAYOUT STATUS UPDATE] Payout {payout_id} : {old_status} → {new_status}")
        
        return JsonResponse({
            'success': True,
            'status': new_status,
            'status_display': payout.get_status_display(),
            'message': f'Statut mis à jour de "{old_status}" vers "{new_status}"'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la mise à jour: {str(e)}'
        })


@staff_member_required
def pending_seller_notifications(request):
    """
    Liste des vendeurs qui n'ont pas répondu aux messages après 2h30
    """
    # Temps limite : 2h30 = 150 minutes
    time_threshold = timezone.now() - timedelta(minutes=150)
    
    # Récupérer tous les chats de transactions actives
    active_chats = Chat.objects.filter(
        transaction__isnull=False,
        transaction__status__in=['pending_payment', 'paid', 'in_progress']
    ).select_related('transaction', 'transaction__buyer', 'transaction__seller')
    
    pending_notifications = []
    
    for chat in active_chats:
        # Récupérer le dernier message de l'acheteur
        last_buyer_message = Message.objects.filter(
            chat=chat,
            sender=chat.transaction.buyer
        ).order_by('-created_at').first()
        
        if not last_buyer_message:
            continue
        
        # Vérifier si le message a plus de 2h30
        if last_buyer_message.created_at > time_threshold:
            continue
        
        # Vérifier s'il y a une réponse du vendeur après ce message
        seller_response = Message.objects.filter(
            chat=chat,
            sender=chat.transaction.seller,
            created_at__gt=last_buyer_message.created_at
        ).exists()
        
        if seller_response:
            continue
        
        # Vérifier si déjà notifié manuellement
        already_notified = PendingEmailNotification.objects.filter(
            transaction=chat.transaction,
            last_buyer_message=last_buyer_message,
            notified_manually=True
        ).exists()
        
        if already_notified:
            continue
        
        # Ajouter à la liste
        pending_notifications.append({
            'transaction': chat.transaction,
            'seller': chat.transaction.seller,
            'seller_email': chat.transaction.seller.email,
            'last_buyer_message': last_buyer_message,
            'time_elapsed': timezone.now() - last_buyer_message.created_at,
            'buyer': chat.transaction.buyer,
        })
    
    context = {
        'pending_notifications': pending_notifications,
        'total_count': len(pending_notifications),
    }
    
    return render(request, 'admin/pending_seller_notifications.html', context)


@staff_member_required
@require_http_methods(["POST"])
def mark_seller_notified(request, transaction_id):
    """
    Marquer un vendeur comme notifié manuellement
    """
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        
        # Récupérer le dernier message de l'acheteur
        chat = Chat.objects.filter(transaction=transaction).first()
        if not chat:
            messages.error(request, "Chat introuvable")
            return redirect('pending_seller_notifications')
        
        last_buyer_message = Message.objects.filter(
            chat=chat,
            sender=transaction.buyer
        ).order_by('-created_at').first()
        
        if not last_buyer_message:
            messages.error(request, "Aucun message de l'acheteur trouvé")
            return redirect('pending_seller_notifications')
        
        # Créer ou mettre à jour la notification
        notification, created = PendingEmailNotification.objects.get_or_create(
            transaction=transaction,
            last_buyer_message=last_buyer_message,
            defaults={
                'seller': transaction.seller,
                'notified_manually': True,
                'notified_at': timezone.now()
            }
        )
        
        if not created:
            notification.notified_manually = True
            notification.notified_at = timezone.now()
            notification.save()
        
        messages.success(request, f"Vendeur @{transaction.seller.username} marqué comme notifié")
        return redirect('pending_seller_notifications')
        
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('pending_seller_notifications')


