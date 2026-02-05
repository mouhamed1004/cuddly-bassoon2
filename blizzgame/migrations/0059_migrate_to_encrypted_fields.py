# Generated manually for data migration to encrypted fields

from django.db import migrations
from blizzgame.encryption_utils import encryption_service
import logging

logger = logging.getLogger(__name__)

def migrate_to_encrypted_fields(apps, schema_editor):
    """
    Migre les données existantes vers les champs chiffrés
    """
    SellerPaymentInfo = apps.get_model('blizzgame', 'SellerPaymentInfo')
    
    logger.info("Début de la migration vers les champs chiffrés...")
    
    # Compter les enregistrements à migrer
    total_records = SellerPaymentInfo.objects.count()
    logger.info(f"Nombre d'enregistrements à migrer: {total_records}")
    
    migrated_count = 0
    
    for payment_info in SellerPaymentInfo.objects.all():
        try:
            # Migrer les données sensibles vers les champs chiffrés
            if payment_info.phone_number:
                payment_info.encrypted_phone_number = payment_info.phone_number
            if payment_info.account_number:
                payment_info.encrypted_account_number = payment_info.account_number
            if payment_info.card_number:
                payment_info.encrypted_card_number = payment_info.card_number
            if payment_info.account_holder_name:
                payment_info.encrypted_account_holder_name = payment_info.account_holder_name
            if payment_info.card_holder_name:
                payment_info.encrypted_card_holder_name = payment_info.card_holder_name
            if payment_info.bank_name:
                payment_info.encrypted_bank_name = payment_info.bank_name
            if payment_info.swift_code:
                payment_info.encrypted_swift_code = payment_info.swift_code
            if payment_info.iban:
                payment_info.encrypted_iban = payment_info.iban
            
            # Sauvegarder sans déclencher les signaux
            payment_info.save(update_fields=[
                'encrypted_phone_number',
                'encrypted_account_number', 
                'encrypted_card_number',
                'encrypted_account_holder_name',
                'encrypted_card_holder_name',
                'encrypted_bank_name',
                'encrypted_swift_code',
                'encrypted_iban'
            ])
            
            migrated_count += 1
            
            if migrated_count % 10 == 0:
                logger.info(f"Migré {migrated_count}/{total_records} enregistrements...")
                
        except Exception as e:
            logger.error(f"Erreur lors de la migration de l'enregistrement {payment_info.id}: {e}")
            continue
    
    logger.info(f"Migration terminée: {migrated_count}/{total_records} enregistrements migrés")

def reverse_migration(apps, schema_editor):
    """
    Annule la migration (copie les données chiffrées vers les champs normaux)
    """
    SellerPaymentInfo = apps.get_model('blizzgame', 'SellerPaymentInfo')
    
    logger.info("Annulation de la migration...")
    
    for payment_info in SellerPaymentInfo.objects.all():
        try:
            # Copier les données chiffrées vers les champs normaux
            if payment_info.encrypted_phone_number:
                payment_info.phone_number = payment_info.encrypted_phone_number
            if payment_info.encrypted_account_number:
                payment_info.account_number = payment_info.encrypted_account_number
            if payment_info.encrypted_card_number:
                payment_info.card_number = payment_info.encrypted_card_number
            if payment_info.encrypted_account_holder_name:
                payment_info.account_holder_name = payment_info.encrypted_account_holder_name
            if payment_info.encrypted_card_holder_name:
                payment_info.card_holder_name = payment_info.encrypted_card_holder_name
            if payment_info.encrypted_bank_name:
                payment_info.bank_name = payment_info.encrypted_bank_name
            if payment_info.encrypted_swift_code:
                payment_info.swift_code = payment_info.encrypted_swift_code
            if payment_info.encrypted_iban:
                payment_info.iban = payment_info.encrypted_iban
            
            payment_info.save()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation pour l'enregistrement {payment_info.id}: {e}")
            continue

class Migration(migrations.Migration):

    dependencies = [
        ('blizzgame', '0058_add_encrypted_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_to_encrypted_fields, reverse_migration),
    ]
