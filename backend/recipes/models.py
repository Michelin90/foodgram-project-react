from django.db import models
from users.models import CustomUser


class Tag(models.Model):
    """Тэги для рецептов"""
    name = models.CharField(
        verbose_name='Название тэга',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=7,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=200,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиенты для рецептов"""
    name = models.CharField(
        verbose_name='Название ингридиента',
        max_length=200
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепты"""
    author = models.ForeignKey(
        CustomUser,
        verbose_name='Автор рецепта',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    text = models.TextField('Описание')
    image = models.ImageField(
        verbose_name='Картинка, закодированная в Base64',
        upload_to='recipes/images/',
        blank=True
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список ингредиентов',
        related_name='recipes',
        through='IngredientRecipe'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Список id тэгов',
        related_name='recipes',
        through='TagRecipe',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)',)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Ингредиенты и их количество в рецепте """
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient_recipe',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredient_recipe',
        on_delete=models.CASCADE
    )
    amount = models.IntegerField()

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='uniqe_ingredient_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class TagRecipe(models.Model):
    """ Тэги в рецепте"""
    tag = models.ForeignKey(
        Tag,
        related_name='recipe',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='tag',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Тэг в рецепте'
        verbose_name_plural = 'Тэги в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='uniqe_tag_recipe'
            )
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class Favorite(models.Model):
    """Избранные рецепты"""
    user = models.ForeignKey(
        CustomUser,
        related_name='favorte',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='uniqe_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class ShoppingCart(models.Model):
    """Рецепты в списке покупок"""
    user = models.ForeignKey(
        CustomUser,
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='uniqe_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'
