# Generated by Django 3.2 on 2023-06-15 13:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20230615_1829'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingridient',
            options={'verbose_name': 'Ингридиент', 'verbose_name_plural': 'Ингридиенты'},
        ),
    ]
