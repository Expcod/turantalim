# Generated by Django 4.2.19 on 2025-03-20 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_remove_user_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, default=None, max_length=254, null=True, unique=True),
        ),
    ]
