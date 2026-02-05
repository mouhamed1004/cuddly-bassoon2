# Generated migration for PendingEmailNotification model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blizzgame', '0099_alter_disputeinformationrequest_response_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingEmailNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notified_manually', models.BooleanField(default=False)),
                ('notified_at', models.DateTimeField(blank=True, null=True)),
                ('last_buyer_message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_trigger', to='blizzgame.message')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pending_seller_notifications', to=settings.AUTH_USER_MODEL)),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pending_notifications', to='blizzgame.transaction')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('transaction', 'last_buyer_message')},
            },
        ),
    ]
