# Generated by Django 5.1.7 on 2025-04-22 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo', '0008_alter_comentario_id_alter_libro_isbn_alter_libro_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='libro',
            name='ISBN',
            field=models.CharField(blank=True, max_length=13),
        ),
        migrations.AlterField(
            model_name='libro',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.DeleteModel(
            name='Comentario',
        ),
    ]
