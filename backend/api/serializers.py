from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import CustomUser, Subscribe

from .core.serializers_utils import Base64ImageField


class UserCreateSerializer(UserCreateSerializer):
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

    def validate_password(self, password):
        """Проверяет пароль на соответсвие минимальной длине.

        Args:
            password (str): Проверяемый пароль.

        Returns:
            password (str): Проверенный пароль.

        Raises:
            ValidationError: Если пароль меньше 8 символов.

        """
        if len(password) < 8:
            raise serializers.ValidationError(
                'Пароль должен состоять как минимум из 8 символов!'
            )
        return password

    def create(self, validated_data):
        """Создаёт нового пользователя.

        Args:
            validated_data (dict):  Проверенные данные.

        Returns:
            User: Созданный пользователь.

        """
        user = CustomUser.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserReadSerialzer(UserSerializer):
    """Сериализатор для чтения объектов модели CustomUser."""

    is_subscribed = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()

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
        """Проверяет наличие подписки у пользователя.

        Опередляет, подписан ли текущий пользователь
        на объект пользователя, полученный для чтения.

        Args:
            obj (CustomUser): Пользователь, на которого проверяется подписка.

        Returns:
            bool: True, если подписан. False, если нет.

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
        """Проверяет полученные данные при изменении пароля.

        Args:
            data (OrderedDict): Проверяемые данные.

        Returns:
            data (OrderedDict): Проверенные данные.

        Raises:
            ValidationError: Если старый пароль совпадает с новым.
            ValidationError: Если пароль меньше 8 символов.

        """
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
        """Заменяет текущий пароль пользователя на новый.

        Args:
            instance (CustomUser): Пользователь, у которого изменяется пароль.
            validated_data (OrderedDict): Проверенные данне.

        Returns:
            instance (CustomUser): Пользователь с измененным паролем.

        """
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class TagSerialzer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRcipeSerialzier(serializers.ModelSerializer):
    """Сериализатор для работы с моделью IngredientRecipe.

    Добавлеяет id ингредиентов и их количество при создании рецепта.

    """

    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        write_only=True,
        min_value=1
    )

    class Meta:
        model = IngredientRecipe
        fields = ('recipe', 'id', 'amount')


class IngredientRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью IngredientRecipe.

    Отображает поля ингредиентов и их количество
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

    def validate_ingredients(self, ingredients):
        """Проверяет полученные данные при добавлении ингредиентов в рецепт.

        Args:
            ingredients (OrderedDict): Проверяемые данные.

        Returns:
            ingredietns (OrderedDict): Проверенные данные.

        Raises:
            ValidationError: Если передан путсой словарь
            ValidationError: Если добавить дважды один и тот же ингредиент.

        """
        if not ingredients:
            raise serializers.ValidationError('Добавьте ингредиент')
        ingredient_list = [
            ingredient.get('ingredient') for ingredient in ingredients
        ]
        if len(ingredient_list) != len(set(ingredient_list)):
            raise serializers.ValidationError(
                'Нельзя добавить дважды один и тот же ингредиент'
            )
        return ingredients

    def validate_tags(self, tags):
        """Проверяет полученные данные при добавлении тэгов в рецепт.

        Args:
            tags (list): Проверяемые данные.

        Returns:
            tags (list): Проверенные данные.

        Raises:
            ValidationError: Если передан путсой словарь
            ValidationError: Если добавить дважды один и тот же ингредиент.

        """
        if not tags:
            raise serializers.ValidationError('Добавьте тэг')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Нельзя добавить дважды один и тот же тэг'
            )
        return tags

    def create(self, validated_data):
        """Создаёт  рецепт.

        Args:
            validated_data (dict): Проверенные данные для создания рецепта.

        Returns:
            Recipe: Созданый рецепт.

        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=ingredient.get('ingredient'),
                    amount=ingredient.get('amount')
                ) for ingredient in ingredients
            ]
        )
        return recipe

    def update(self, instance, validated_data):
        """Изменяет рецепт.

        Args:
            instance (Recipe): Изменяемый рецепт.
            validated_data (dict): Проверенные данные для изменения рецепта.

        Returns:
            Recipe: Измененный рецепт.

        """
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
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredients.clear()
            IngredientRecipe.objects.bulk_create(
                [
                    IngredientRecipe(
                        recipe=instance,
                        amount=ingredient.get('amount'),
                        ingredient=ingredient.get('ingredient')
                    ) for ingredient in ingredients_data
                ]
            )
        instance.save()
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Фрмирует данные для чтения.

        Args:
            instance (Recipe): Рецепт(ты).

        Returns
            serializer.data (dict): Рецепт(ты) для чтения.

        """
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
        """Определяет, добавлен ли рецепт в избранное текущего пользоватлея.

        Args:
            obj (Recipe): Проверяемый рецепт.

        Returns:
            bool: True, если рецепт в избранном. False, если нет.

        """
        request = self.context.get('request')
        return Favorite.objects.filter(
            user=request.user.id,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Определяет, добавлен ли рецепт в список покупок пользоватлея.

        Args:
            obj (Recipe): Проверяемый рецепт.

        Returns:
            bool: True, если рецепт в списке покупок. False, если нет.

        """
        request = self.context.get('request')
        return ShoppingCart.objects.filter(
            user=request.user.id,
            recipe=obj
        ).exists()


class RecipeShortListSerializer(serializers.ModelSerializer):
    """Сериализатор для работы моделью Recipe.

    Используется там, где для чтения нужно вывести
    неполное количество полей этой модели.

    """

    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )

    def validate(self, data):
        """Проводит проверку данных при добавлении или удалении объекта.

        Args:
            data (None): Пустой словарь данных.

        Returns:
            data (None): Пустой словарь данных.

        Raises:
            ValidatonError: Если остутсвует объект удаления.
            ValidatonError: Если объект уже создан.

        """
        request = self.context.get('request')
        recipe = self.instance
        model = self.context.get('model')
        if request.method == "DELETE":
            if not model.objects.filter(
                recipe=recipe,
                user=request.user
            ).exists():
                raise serializers.ValidationError(
                    {"errors": "Отсутствует объект удаления"}
                )
            return data
        if model.objects.filter(
            recipe=recipe,
            user=request.user
        ).exists():
            raise serializers.ValidationError(
                {'errors': 'Объект уже добавлен.'}
            )
        return data


class SubscribeSerializer(UserReadSerialzer):
    """Сериализатор для работы с моделью CustomUser.

    Используется для создания подписки текущего пользователя
    на автора рецепта.

    """

    recipes = serializers.SerializerMethodField()
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

    def validate(self, data):
        """Проводит проверку данных при добавлении или удалении подписки.

        Args:
            data (None): Пустой словарь данных.

        Returns:
            data (None): Пустой словарь данных.

        Raises:
            ValidatonError: Если остутсвует объект удаления подписки.
            ValidatonError: Если подписка уже создана.
            ValidatonError: Если пытаются подписаться на самого себя.

        """
        request = self.context.get('request')
        subscribing = self.instance
        if request.method == "DELETE":
            if not Subscribe.objects.filter(
                subscribing=subscribing,
                user=request.user
            ).exists():
                raise serializers.ValidationError(
                    {"errors": "Подписка на этого автора еще не оформлена"}
                )
            return data
        if subscribing == request.user:
            raise serializers.ValidationError(
                {"errors": "Нельзя подписаться на самого себя"}
            )
        if Subscribe.objects.filter(
            subscribing=subscribing,
            user=request.user
        ).exists():
            raise serializers.ValidationError(
                {"errors": "Подписка на этого автора уже оформлена"}
            )
        return data

    def get_recipes(self, obj):
        """Предоставляет спискок рецептов автора.

        Args:
            obj (CustomUser): Автор.

        Returns:
            serializer.data (dict): Список рецептов автора.

        """
        limit = self.context.get('request').GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeShortListSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """Определяет количество рецептов у автора.

        Args:
            obj (CustomUser): Автор, на которого осуществлена подписка.

        Returns:
            obj.recipes.count (int): Количество рецептов у автора.

        """
        return obj.recipes.count()
