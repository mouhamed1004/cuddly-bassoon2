# Generated migration for CloudinaryField

from django.db import migrations
import cloudinary.models


class Migration(migrations.Migration):

    dependencies = [
        ('blizzgame', '0067_add_order_to_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disputeinformationrequest',
            name='response_file',
            field=cloudinary.models.CloudinaryField(blank=True, help_text='Fichier uploadé en réponse', max_length=255, null=True, verbose_name='dispute_response'),
        ),
    ]
