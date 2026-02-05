# Generated manually on 2025-09-27 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blizzgame', '0065_add_payout_type_to_payoutrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='payoutrequest',
            name='original_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Montant original de la transaction', max_digits=10, null=True),
        ),
    ]
