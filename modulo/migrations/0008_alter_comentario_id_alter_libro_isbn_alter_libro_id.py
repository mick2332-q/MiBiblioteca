# Generated by Django 5.1.7 on 2025-04-22 22:05

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo', '0007_comentario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comentario',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='libro',
            name='ISBN',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
        migrations.AlterField(
            model_name='libro',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
