# Generated manually on 2025-09-27 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blizzgame', '0064_chat_dispute_chat_is_active_chat_is_locked_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='payoutrequest',
            name='payout_type',
            field=models.CharField(
                choices=[
                    ('seller_payout', 'Paiement Vendeur'),
                    ('buyer_refund', 'Remboursement Acheteur'),
                ],
                default='seller_payout',
                help_text='Type de payout',
                max_length=20
            ),
        ),
    ]
