from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from recipes.models import IngredientRecipe, Recipe
from rest_framework import response, status

from ..serializers import RecipeShortListSerializer


def post_delete_object(request, pk, model):
    """"
    Функция для создания и удаления объектов
    классов Favortie и ShoppingCart.
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


def get_paginated_qeryset(self, seriazlizer_class, queryset, request):
    """
    Функция, возвращающая пагнированный список объектов указанного класса.
    """
    page = self.paginate_queryset(queryset.order_by('-id'))
    if page is not None:
        serializer = seriazlizer_class(
            page,
            many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)
    serializer = seriazlizer_class(
        queryset,
        many=True,
        context={'request': request})
    return response.Response(serializer.data)


def create_and_download_file(request):
    """
    Метод, мдели IngredientRecipe, возвращающий текстовый документ, содержащий
    список ингредиентов и их количество для рецептов,
    которые находятся в списке покупок текущего пользователя.
    """
    ingredients = IngredientRecipe.objects.filter(
        recipe__shopping_cart__user=request.user
    ).values_list(
        'ingredient__name', 'ingredient__measurement_unit',
    ).annotate(Sum('amount'))
    shopping_cart = 'Список покупок\n\n'
    shopping_cart += '\n'.join([
        '{0} - {2}{1}.' .format(*ingredient) for ingredient in ingredients
    ])
    response = HttpResponse(shopping_cart, content_type='application/txt')
    response['Content-Disposition'] = 'attachment; filename="file.txt"'
    return response
