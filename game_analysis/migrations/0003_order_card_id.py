# Generated by Django 2.2.3 on 2019-08-23 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game_analysis', '0002_initialize_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='card_id',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]