# Generated by Django 4.2.19 on 2025-03-20 18:39

import apps.users.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_alter_user_email'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', apps.users.models.CustomUserManager()),
            ],
        ),
    ]
