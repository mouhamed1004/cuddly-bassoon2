#!/usr/bin/env python3
"""
Commande de nettoyage des transactions abandonnées.
Cette commande nettoie les transactions qui sont restées en 'processing' 
sans paiement CinetPay validé pendant plus de 2 heures.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from blizzgame.models import Transaction, CinetPayTransaction, Post, Notification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Nettoie les transactions abandonnées (processing sans paiement validé)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule le nettoyage sans effectuer de modifications',
        )
        parser.add_argument(
            '--timeout-hours',
            type=int,
            default=2,
            help='Timeout en heures pour considérer une transaction comme abandonnée',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        timeout_hours = options['timeout_hours']
        
        self.stdout.write(
            self.style.SUCCESS(f'🧹 Début du nettoyage des transactions abandonnées (timeout: {timeout_hours}h)')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Mode simulation activé - aucune modification ne sera effectuée'))
        
        # Calculer la date limite
        abandoned_time = timezone.now() - timedelta(hours=timeout_hours)
        
        # Trouver les transactions abandonnées
        # Transactions en 'processing' sans paiement CinetPay validé
        abandoned_transactions = Transaction.objects.filter(
            status='processing',
            created_at__lt=abandoned_time
        ).exclude(
            cinetpay_transaction__status__in=['payment_received', 'in_escrow', 'escrow_released', 'completed']
        ).select_related('post', 'buyer', 'seller')
        
        self.stdout.write(f'📊 {abandoned_transactions.count()} transactions abandonnées trouvées')
        
        if abandoned_transactions.count() == 0:
            self.stdout.write(self.style.SUCCESS('✅ Aucune transaction abandonnée à nettoyer'))
            return
        
        # Traiter chaque transaction abandonnée
        cleaned_count = 0
        for transaction in abandoned_transactions:
            try:
                self.stdout.write(f'🔄 Traitement de la transaction {transaction.id}')
                
                if not dry_run:
                    # Annuler la transaction
                    transaction.status = 'cancelled'
                    transaction.save()
                    
                    # Annuler la transaction CinetPay si elle existe
                    if hasattr(transaction, 'cinetpay_transaction'):
                        cinetpay = transaction.cinetpay_transaction
                        cinetpay.status = 'cancelled'
                        cinetpay.save()
                        self.stdout.write(f'   ✅ Transaction CinetPay annulée: {cinetpay.id}')
                    
                    # Libérer l'annonce - la remettre en vente
                    post = transaction.post
                    post.is_in_transaction = False
                    post.is_on_sale = True
                    post.is_sold = False
                    post.save()
                    self.stdout.write(f'   ✅ Annonce remise en vente: {post.title}')
                    
                    # Créer une notification pour le vendeur
                    Notification.objects.create(
                        user=transaction.seller,
                        type='transaction_cancelled',
                        title='Transaction annulée (abandonnée)',
                        content=f"La transaction pour '{post.title}' a été annulée automatiquement car le paiement n'a pas été finalisé dans les {timeout_hours} heures imparties. Votre annonce est maintenant disponible à la vente.",
                        transaction=transaction
                    )
                    self.stdout.write(f'   ✅ Notification envoyée au vendeur: {transaction.seller.username}')
                    
                    # Créer une notification pour l'acheteur
                    Notification.objects.create(
                        user=transaction.buyer,
                        type='transaction_cancelled',
                        title='Transaction annulée (abandonnée)',
                        content=f"Votre transaction pour '{post.title}' a été annulée automatiquement car le paiement n'a pas été finalisé dans les {timeout_hours} heures imparties.",
                        transaction=transaction
                    )
                    self.stdout.write(f'   ✅ Notification envoyée à l\'acheteur: {transaction.buyer.username}')
                
                cleaned_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur lors du traitement de la transaction {transaction.id}: {e}')
                )
                logger.error(f'Erreur lors du nettoyage de la transaction {transaction.id}: {e}')
        
        # Résumé
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'🔍 Simulation terminée: {cleaned_count} transactions seraient nettoyées')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Nettoyage terminé: {cleaned_count} transactions nettoyées')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Nettoyage des transactions abandonnées terminé!')
        )