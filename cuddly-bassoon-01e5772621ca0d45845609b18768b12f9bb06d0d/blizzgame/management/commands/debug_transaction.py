#!/usr/bin/env python3
"""
Commande de diagnostic pour vérifier les transactions et identifier les problèmes.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from blizzgame.models import Transaction, CinetPayTransaction, Post
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Diagnostique les transactions et identifie les problèmes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--transaction-id',
            type=str,
            help='ID de transaction spécifique à diagnostiquer',
        )
        parser.add_argument(
            '--recent',
            action='store_true',
            help='Afficher les transactions récentes',
        )

    def handle(self, *args, **options):
        if options['transaction_id']:
            self.diagnose_transaction(options['transaction_id'])
        elif options['recent']:
            self.show_recent_transactions()
        else:
            self.show_transaction_stats()

    def diagnose_transaction(self, transaction_id):
        """Diagnostique une transaction spécifique"""
        self.stdout.write(f'🔍 Diagnostic de la transaction {transaction_id}')
        
        try:
            # Vérifier si la transaction existe
            try:
                transaction = Transaction.objects.get(id=transaction_id)
                self.stdout.write(f'✅ Transaction trouvée: {transaction.id}')
                self.stdout.write(f'   - Statut: {transaction.status}')
                self.stdout.write(f'   - Acheteur: {transaction.buyer.username}')
                self.stdout.write(f'   - Vendeur: {transaction.seller.username}')
                self.stdout.write(f'   - Montant: {transaction.amount}')
                self.stdout.write(f'   - Créée le: {transaction.created_at}')
                self.stdout.write(f'   - Modifiée le: {transaction.updated_at}')
                
                # Vérifier l'annonce
                post = transaction.post
                self.stdout.write(f'📦 Annonce: {post.title}')
                self.stdout.write(f'   - ID: {post.id}')
                self.stdout.write(f'   - En vente: {post.is_on_sale}')
                self.stdout.write(f'   - En transaction: {post.is_in_transaction}')
                self.stdout.write(f'   - Vendue: {post.is_sold}')
                
                # Vérifier la transaction CinetPay
                if hasattr(transaction, 'cinetpay_transaction'):
                    cinetpay = transaction.cinetpay_transaction
                    self.stdout.write(f'💳 Transaction CinetPay: {cinetpay.id}')
                    self.stdout.write(f'   - Statut: {cinetpay.status}')
                    self.stdout.write(f'   - Montant: {cinetpay.amount}')
                    self.stdout.write(f'   - Créée le: {cinetpay.created_at}')
                else:
                    self.stdout.write('❌ Aucune transaction CinetPay associée')
                    
            except Transaction.DoesNotExist:
                self.stdout.write(f'❌ Transaction {transaction_id} non trouvée')
                
                # Chercher des transactions similaires
                similar_transactions = Transaction.objects.filter(
                    id__icontains=transaction_id[:8]
                )[:5]
                
                if similar_transactions:
                    self.stdout.write('🔍 Transactions similaires trouvées:')
                    for t in similar_transactions:
                        self.stdout.write(f'   - {t.id} ({t.status}) - {t.created_at}')
                else:
                    self.stdout.write('❌ Aucune transaction similaire trouvée')
                    
        except Exception as e:
            self.stdout.write(f'❌ Erreur lors du diagnostic: {e}')

    def show_recent_transactions(self):
        """Affiche les transactions récentes"""
        self.stdout.write('📊 Transactions récentes (dernières 24h)')
        
        recent_time = timezone.now() - timezone.timedelta(hours=24)
        transactions = Transaction.objects.filter(
            created_at__gte=recent_time
        ).order_by('-created_at')[:20]
        
        if not transactions:
            self.stdout.write('❌ Aucune transaction récente')
            return
            
        for transaction in transactions:
            self.stdout.write(f'   - {transaction.id} ({transaction.status}) - {transaction.buyer.username} -> {transaction.seller.username} - {transaction.amount}€')

    def show_transaction_stats(self):
        """Affiche les statistiques des transactions"""
        self.stdout.write('📊 Statistiques des transactions')
        
        total = Transaction.objects.count()
        pending = Transaction.objects.filter(status='pending').count()
        processing = Transaction.objects.filter(status='processing').count()
        completed = Transaction.objects.filter(status='completed').count()
        failed = Transaction.objects.filter(status='failed').count()
        cancelled = Transaction.objects.filter(status='cancelled').count()
        disputed = Transaction.objects.filter(status='disputed').count()
        
        self.stdout.write(f'   - Total: {total}')
        self.stdout.write(f'   - En attente: {pending}')
        self.stdout.write(f'   - En cours: {processing}')
        self.stdout.write(f'   - Terminées: {completed}')
        self.stdout.write(f'   - Échouées: {failed}')
        self.stdout.write(f'   - Annulées: {cancelled}')
        self.stdout.write(f'   - En litige: {disputed}')
        
        # Vérifier les transactions CinetPay
        cinetpay_total = CinetPayTransaction.objects.count()
        cinetpay_pending = CinetPayTransaction.objects.filter(status='pending_payment').count()
        cinetpay_received = CinetPayTransaction.objects.filter(status='payment_received').count()
        
        self.stdout.write(f'💳 Transactions CinetPay:')
        self.stdout.write(f'   - Total: {cinetpay_total}')
        self.stdout.write(f'   - En attente de paiement: {cinetpay_pending}')
        self.stdout.write(f'   - Paiement reçu: {cinetpay_received}')

