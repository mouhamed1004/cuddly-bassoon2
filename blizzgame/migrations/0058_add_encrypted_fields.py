# Generated manually for encryption migration

from django.db import migrations, models
import blizzgame.encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('blizzgame', '0046_passwordreset'),
    ]

    operations = [
        # Ajouter les nouveaux champs chiffrés
        migrations.AddField(
            model_name='sellerpaymentinfo',
            name='encrypted_phone_number',
            field=blizzgame.encrypted_fields.EncryptedCharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='sellerpaymentinfo',
            name='encrypted_account_number',
            field=blizzgame.encrypted_fields.EncryptedCharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='sellerpaymentinfo',
            name='encrypted_card_number',
            field=blizzgame.encrypted_fields.EncryptedCharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='sellerpaymentinfo',
            name='encrypted_account_holder_name',
            field=blizzgame.encrypted_fields.EncryptedCharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='sellerpaymentinfo',
            name='encrypted_card_holder_name',
            field=blizzgame.encrypted_fields.EncryptedCharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='sellerpaymentinfo',
            name='encrypted_bank_name',
            field=blizzgame.encrypted_fields.EncryptedCharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='sellerpaymentinfo',
            name='encrypted_swift_code',
            field=blizzgame.encrypted_fields.EncryptedCharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='sellerpaymentinfo',
            name='encrypted_iban',
            field=blizzgame.encrypted_fields.EncryptedCharField(blank=True, max_length=50, null=True),
        ),
    ]
