# Generated by Django 3.2 on 2023-06-16 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_auto_20230616_2057'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='cooking_time',
            field=models.IntegerField(default=1, verbose_name='Время приготовления (в минутах)'),
            preserve_default=False,
        ),
    ]
