# Generated by Django 5.1.1 on 2024-09-29 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eduMaterial', '0004_educationalmaterial_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationalmaterial',
            name='file_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
