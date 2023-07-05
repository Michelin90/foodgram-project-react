from django.db.models import Sum
from django.shortcuts import get_object_or_404
from recipes.models import IngredientRecipe, Recipe
from rest_framework import response, status

from ..serializers import RecipeShortListSerializer


def post_delete_object(request, pk, model):
    """"Создает или удаляет объекты моделей Favortie и ShoppingCart.

     Args:
        request (HttpRequest):  Объект запроса.
        pk (int): id  добавляемого или удаляемого рецепта.
        model(ModelBase): Модель, объект которой необходимо создать/удалить.

    Returns:
        Response: Cтатус подтверждающий или запрещающий выбранное действие.

    """
    recipe = get_object_or_404(Recipe, pk=pk)
    serializer = RecipeShortListSerializer(
        recipe,
        data=request.data,
        context={'request': request, 'model': model}
    )
    if request.method == 'POST':
        serializer.is_valid(raise_exception=True)
        model.objects.create(
            user=request.user,
            recipe=recipe
        )
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED)
    serializer.is_valid(raise_exception=True)
    model.objects.filter(
        user=request.user,
        recipe=recipe
    ).delete()
    return response.Response(status=status.HTTP_204_NO_CONTENT)


def get_paginated_queryset(self, serializer_class, queryset, request):
    """Возвращающает пагнированный список объектов указанного класса.

     Args:
        serializer_class (SerializerMetaclass): Сериализатор.
        queryset (list[ModelBase]): Список обьектов указанного класса.
        request (HttpResponse): Объект запроса.

    Returns:
        Response:  Пагинированный список обьектов указанного класса.

    """
    page = self.paginate_queryset(queryset.order_by('-id'))
    if page is not None:
        serializer = serializer_class(
            page,
            many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)
    serializer = serializer_class(
        queryset,
        many=True,
        context={'request': request})
    return response.Response(serializer.data)


def create_and_download_file(user):
    """Создает обьект со списком покупок.

    Args:
        user (CustomUser): Текущий пользователь.

    Returns:
        shopping_cart (str): Oбьект со списком покупок текущего пользователя.

    """
    ingredients = IngredientRecipe.objects.filter(
        recipe__shopping_cart__user=user
    ).values_list(
        'ingredient__name', 'ingredient__measurement_unit',
    ).annotate(Sum('amount'))
    shopping_cart = 'Список покупок\n\n'
    shopping_cart += '\n'.join([
        '{0} - {2}{1}.' .format(*ingredient) for ingredient in ingredients
    ])
    return shopping_cart
