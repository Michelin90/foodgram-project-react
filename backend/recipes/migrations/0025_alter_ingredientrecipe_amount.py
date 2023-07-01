# Generated by Django 3.2 on 2023-06-30 05:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0024_auto_20230630_0048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientrecipe',
            name='amount',
            field=models.IntegerField(error_messages={'validators': 'Минимальное количество ингредиента в рецепте = 1'}, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество ингредиента в рецепте'),
        ),
    ]