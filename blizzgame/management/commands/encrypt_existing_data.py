"""
Commande Django pour chiffrer les données sensibles existantes
ATTENTION: Cette commande doit être exécutée avec prudence
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from blizzgame.models import SellerPaymentInfo, CinetPayTransaction, ShopCinetPayTransaction
from blizzgame.encryption_utils import encrypt_sensitive_data, is_data_encrypted
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Chiffre les données sensibles existantes dans la base de données'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule le chiffrement sans modifier la base de données',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Chiffre seulement un modèle spécifique (SellerPaymentInfo, CinetPayTransaction, ShopCinetPayTransaction)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Taille des lots pour le traitement (défaut: 100)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        model_name = options.get('model')
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.WARNING('🔐 DÉBUT DU CHIFFREMENT DES DONNÉES SENSIBLES')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  MODE DRY-RUN - Aucune modification ne sera effectuée')
            )
        
        try:
            # Vérifier que le chiffrement fonctionne
            test_data = "test_encryption_123"
            encrypted = encrypt_sensitive_data(test_data)
            if not encrypted or encrypted == test_data:
                raise CommandError("Le système de chiffrement ne fonctionne pas correctement")
            
            self.stdout.write(
                self.style.SUCCESS('✅ Système de chiffrement opérationnel')
            )
            
            # Chiffrer les données par modèle
            if not model_name or model_name == 'SellerPaymentInfo':
                self.encrypt_seller_payment_info(dry_run, batch_size)
            
            if not model_name or model_name == 'CinetPayTransaction':
                self.encrypt_cinetpay_transactions(dry_run, batch_size)
            
            if not model_name or model_name == 'ShopCinetPayTransaction':
                self.encrypt_shop_cinetpay_transactions(dry_run, batch_size)
            
            self.stdout.write(
                self.style.SUCCESS('🎉 Chiffrement terminé avec succès!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors du chiffrement: {e}')
            )
            raise CommandError(f'Chiffrement échoué: {e}')
    
    def encrypt_seller_payment_info(self, dry_run, batch_size):
        """Chiffre les informations de paiement des vendeurs"""
        self.stdout.write('📱 Chiffrement des informations de paiement des vendeurs...')
        
        # Champs sensibles à chiffrer
        sensitive_fields = [
            'phone_number',
            'account_number', 
            'swift_code',
            'iban',
            'card_number'
        ]
        
        total_updated = 0
        
        # Traitement par lots
        queryset = SellerPaymentInfo.objects.all()
        total_count = queryset.count()
        
        self.stdout.write(f'   📊 {total_count} enregistrements à traiter')
        
        for i in range(0, total_count, batch_size):
            batch = queryset[i:i + batch_size]
            
            with transaction.atomic():
                for payment_info in batch:
                    updated = False
                    
                    for field_name in sensitive_fields:
                        field_value = getattr(payment_info, field_name, None)
                        
                        if field_value and field_value.strip() and not is_data_encrypted(field_value):
                            if not dry_run:
                                encrypted_value = encrypt_sensitive_data(field_value)
                                setattr(payment_info, field_name, encrypted_value)
                                updated = True
                            else:
                                self.stdout.write(f'   🔐 {field_name}: {field_value[:10]}... -> [CHIFFRÉ]')
                    
                    if updated and not dry_run:
                        payment_info.save(update_fields=sensitive_fields)
                        total_updated += 1
                
                if not dry_run:
                    self.stdout.write(f'   ✅ Lot {i//batch_size + 1} traité ({len(batch)} enregistrements)')
        
        if dry_run:
            self.stdout.write(f'   📊 Simulation: {total_count} enregistrements seraient chiffrés')
        else:
            self.stdout.write(f'   ✅ {total_updated} enregistrements chiffrés')
    
    def encrypt_cinetpay_transactions(self, dry_run, batch_size):
        """Chiffre les transactions CinetPay"""
        self.stdout.write('💳 Chiffrement des transactions CinetPay...')
        
        # Champs sensibles à chiffrer
        sensitive_fields = [
            'customer_phone_number',
            'customer_email',
            'seller_phone_number'
        ]
        
        total_updated = 0
        
        # Traitement par lots
        queryset = CinetPayTransaction.objects.all()
        total_count = queryset.count()
        
        self.stdout.write(f'   📊 {total_count} enregistrements à traiter')
        
        for i in range(0, total_count, batch_size):
            batch = queryset[i:i + batch_size]
            
            with transaction.atomic():
                for cinetpay_transaction in batch:
                    updated = False
                    
                    for field_name in sensitive_fields:
                        field_value = getattr(cinetpay_transaction, field_name, None)
                        
                        if field_value and field_value.strip() and not is_data_encrypted(field_value):
                            if not dry_run:
                                encrypted_value = encrypt_sensitive_data(field_value)
                                setattr(cinetpay_transaction, field_name, encrypted_value)
                                updated = True
                            else:
                                self.stdout.write(f'   🔐 {field_name}: {field_value[:10]}... -> [CHIFFRÉ]')
                    
                    if updated and not dry_run:
                        cinetpay_transaction.save(update_fields=sensitive_fields)
                        total_updated += 1
                
                if not dry_run:
                    self.stdout.write(f'   ✅ Lot {i//batch_size + 1} traité ({len(batch)} enregistrements)')
        
        if dry_run:
            self.stdout.write(f'   📊 Simulation: {total_count} enregistrements seraient chiffrés')
        else:
            self.stdout.write(f'   ✅ {total_updated} enregistrements chiffrés')
    
    def encrypt_shop_cinetpay_transactions(self, dry_run, batch_size):
        """Chiffre les transactions CinetPay de la boutique"""
        self.stdout.write('🛒 Chiffrement des transactions boutique CinetPay...')
        
        # Champs sensibles à chiffrer
        sensitive_fields = [
            'customer_phone_number',
            'customer_email'
        ]
        
        total_updated = 0
        
        # Traitement par lots
        queryset = ShopCinetPayTransaction.objects.all()
        total_count = queryset.count()
        
        self.stdout.write(f'   📊 {total_count} enregistrements à traiter')
        
        for i in range(0, total_count, batch_size):
            batch = queryset[i:i + batch_size]
            
            with transaction.atomic():
                for shop_transaction in batch:
                    updated = False
                    
                    for field_name in sensitive_fields:
                        field_value = getattr(shop_transaction, field_name, None)
                        
                        if field_value and field_value.strip() and not is_data_encrypted(field_value):
                            if not dry_run:
                                encrypted_value = encrypt_sensitive_data(field_value)
                                setattr(shop_transaction, field_name, encrypted_value)
                                updated = True
                            else:
                                self.stdout.write(f'   🔐 {field_name}: {field_value[:10]}... -> [CHIFFRÉ]')
                    
                    if updated and not dry_run:
                        shop_transaction.save(update_fields=sensitive_fields)
                        total_updated += 1
                
                if not dry_run:
                    self.stdout.write(f'   ✅ Lot {i//batch_size + 1} traité ({len(batch)} enregistrements)')
        
        if dry_run:
            self.stdout.write(f'   📊 Simulation: {total_count} enregistrements seraient chiffrés')
        else:
            self.stdout.write(f'   ✅ {total_updated} enregistrements chiffrés')
