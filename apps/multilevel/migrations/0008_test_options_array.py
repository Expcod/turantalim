# Generated by Django 4.2.19 on 2025-03-12 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multilevel', '0007_alter_useranswer_is_correct'),
    ]

    operations = [
        migrations.AddField(
            model_name='test',
            name='options_array',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Variantlar textlari'),
        ),
    ]
