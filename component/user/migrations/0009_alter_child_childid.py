# Generated by Django 5.1.1 on 2024-09-26 09:44

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_parent_is_active_parent_is_staff_parent_is_superuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='child',
            name='childID',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
