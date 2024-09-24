# Generated by Django 5.1.1 on 2024-09-23 16:42

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_delete_customuser_parent_last_login'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parent',
            name='parentID',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
