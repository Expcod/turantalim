# Generated by Django 4.2.19 on 2025-04-03 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0005_remove_exampayment_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exampayment',
            name='amount',
            field=models.IntegerField(verbose_name='To‘lov miqdori'),
        ),
    ]
