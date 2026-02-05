#!/usr/bin/env python3
"""
Commande de nettoyage automatique des transactions expirées.
Cette commande doit être exécutée régulièrement (toutes les 5 minutes) via cron.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from blizzgame.models import Transaction, CinetPayTransaction, Post, Notification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Nettoie les transactions expirées et libère les annonces bloquées'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule le nettoyage sans effectuer de modifications',
        )
        parser.add_argument(
            '--timeout-minutes',
            type=int,
            default=getattr(settings, 'PAYMENT_TIMEOUT_MINUTES', 30),
            help='Timeout en minutes pour considérer une transaction comme expirée',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        timeout_minutes = options['timeout_minutes']
        
        self.stdout.write(
            self.style.SUCCESS(f'🧹 Début du nettoyage des transactions expirées (timeout: {timeout_minutes}min)')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Mode simulation activé - aucune modification ne sera effectuée'))
        
        # Calculer la date limite
        expired_time = timezone.now() - timedelta(minutes=timeout_minutes)
        
        # Trouver les transactions expirées
        expired_transactions = Transaction.objects.filter(
            status='pending',
            created_at__lt=expired_time
        ).select_related('post', 'buyer', 'seller')
        
        self.stdout.write(f'📊 {expired_transactions.count()} transactions expirées trouvées')
        
        if expired_transactions.count() == 0:
            self.stdout.write(self.style.SUCCESS('✅ Aucune transaction expirée à nettoyer'))
            return
        
        # Traiter chaque transaction expirée
        cleaned_count = 0
        for transaction in expired_transactions:
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
                    
                    # Libérer l'annonce
                    post = transaction.post
                    post.is_in_transaction = False
                    post.save()
                    self.stdout.write(f'   ✅ Annonce libérée: {post.title}')
                    
                    # Créer une notification pour le vendeur
                    Notification.objects.create(
                        user=transaction.seller,
                        type='transaction_cancelled',
                        title='Transaction annulée (timeout)',
                        content=f"La transaction pour '{post.title}' a été annulée automatiquement car le paiement n'a pas été effectué dans les {timeout_minutes} minutes imparties. Votre annonce est maintenant disponible à la vente.",
                        transaction=transaction
                    )
                    self.stdout.write(f'   ✅ Notification envoyée au vendeur: {transaction.seller.username}')
                    
                    # Créer une notification pour l'acheteur
                    Notification.objects.create(
                        user=transaction.buyer,
                        type='transaction_cancelled',
                        title='Transaction annulée (timeout)',
                        content=f"Votre transaction pour '{post.title}' a été annulée automatiquement car le paiement n'a pas été effectué dans les {timeout_minutes} minutes imparties.",
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
        
        # Nettoyer aussi les transactions CinetPay orphelines
        self.cleanup_orphaned_cinetpay_transactions(dry_run)
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Nettoyage des transactions expirées terminé!')
        )

    def cleanup_orphaned_cinetpay_transactions(self, dry_run=False):
        """Nettoie les transactions CinetPay orphelines"""
        self.stdout.write('🔍 Recherche des transactions CinetPay orphelines...')
        
        # Trouver les transactions CinetPay sans transaction associée
        orphaned_cinetpay = CinetPayTransaction.objects.filter(
            status='pending_payment',
            created_at__lt=timezone.now() - timedelta(minutes=getattr(settings, 'PAYMENT_TIMEOUT_MINUTES', 30))
        )
        
        orphaned_count = orphaned_cinetpay.count()
        self.stdout.write(f'📊 {orphaned_count} transactions CinetPay orphelines trouvées')
        
        if orphaned_count > 0 and not dry_run:
            orphaned_cinetpay.update(status='cancelled')
            self.stdout.write(f'✅ {orphaned_count} transactions CinetPay orphelines annulées')
        elif dry_run:
            self.stdout.write(f'🔍 Simulation: {orphaned_count} transactions CinetPay seraient annulées')

