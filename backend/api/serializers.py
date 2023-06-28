import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag, TagRecipe)
from rest_framework import serializers
from users.models import CustomUser, Subscribe


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания объекта модели CustomUser."""

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                'Пароль должен состоять как минимум из 8 символов!'
            )
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserReadSerialzer(serializers.ModelSerializer):
    """Сериализатор для чтения объектов модели CustomUser."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """
        Метод для проверки наличия подписки у текущего пользователя
        на объект пользователя, полученный для чтения.
        """
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            subscribing=obj, user=request.user
            ).exists()


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля текущего пользователя."""
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)

    def validate(self, data):
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError(
                'Новый пароль не должен совпадать со старым!'
            )
        if len(data['new_password']) < 8:
            raise serializers.ValidationError(
                'Пароль должен состоять как минимум из 8 символов!'
            )
        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class Base64ImageField(serializers.ImageField):
    """Сериализатор для конвертации текстовой строки в файл изображения."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp' + ext)
        return super().to_internal_value(data)


class TagSerialzer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Tag."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Ingredient."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRcipeSerialzier(serializers.Serializer):
    """
    Сериализатор для добавления id ингредиентов и их количества
    при создании рецепта.
    """
    amount = serializers.IntegerField()
    id = serializers.IntegerField()


class IngredientRecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения полей ингредиентов и их количества
    в рецепте, предоставленном для чтения.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.ReadOnlyField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCerateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания или обновления объекта модели Recipe."""
    author = UserReadSerialzer(read_only=True)
    ingredients = IngredientRcipeSerialzier(many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        print(value)
        if len(value) == 0:
            raise serializers.ValidationError('Добавьте ингредиент')
        for i in value:
            if 'id' not in i:
                raise serializers.ValidationError(
                    'Пропущено обязательное поле id'
                )
            if 'amount' not in i:
                raise serializers.ValidationError(
                    'Пропущено обязательное поле amount'
                )
        return value

    def validate_tags(self, value):
        if len(value) == 0:
            raise serializers.ValidationError('Добавьте тэг')
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше одной минуты'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        for ingr in ingredients:
            current_ingredient = get_object_or_404(Ingredient, pk=ingr['id'])
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingr['amount']
            )
        for tag in tags:
            current_tag = get_object_or_404(Tag, pk=tag.id)
            TagRecipe.objects.create(
                tag=current_tag,
                recipe=recipe
            )
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)
        if 'ingredients' in validated_data:
            lst = []
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredients.clear()
            for ingr in ingredients_data:
                current_ingredient = get_object_or_404(
                    Ingredient, pk=ingr['id']
                    )
                IngredientRecipe.objects.create(
                    recipe=instance,
                    ingredient=current_ingredient,
                    amount=ingr['amount']
                )
                lst.append(current_ingredient)
            instance.ingredients.set(lst)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        serializer = RecipeReadSerializer(
            instance, context={'request': request}
        )
        return serializer.data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения объектов модели Recipe."""
    author = UserReadSerialzer(read_only=True)
    ingredients = IngredientRecipeReadSerializer(
        many=True,
        source='ingredient_recipe'
    )
    image = Base64ImageField(read_only=True)
    tags = TagSerialzer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        """
        Метод для определения факта нахождения или отсутсвия
        рецепта в списке избранного текущего пользователя.
        """
        request = self.context.get('request')
        return Favorite.objects.filter(
            user=request.user.id,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Метод для определения факта нахождения или отсутсвия
        рецепта в списке покупок текущего пользователя.
        """
        request = self.context.get('request')
        return ShoppingCart.objects.filter(
            user=request.user.id,
            recipe=obj
        ).exists()


class RecipeShortListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы моделью Recipe там, где для
    чтения нужно вывести неполное количество полей этой модели.
    """

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscribeSerializer(UserReadSerialzer):
    """
    Сериализатор для создания подписки текущего пользователя
    на автора рецепта.
    """
    recipes = RecipeShortListSerializer(many=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserReadSerialzer.Meta):
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, obj):
        """
        Метод определения количества рецептов у автора,
        на которого осуществлена подписка текущим пользовталем.
        """
        return obj.recipes.count()
