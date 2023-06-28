from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import response, serializers, status

from .serializers import RecipeShortListSerializer


def post_delete_object(request, pk, model):
    """"
    Функция для создания и удаления объектов
    классов Favortie и ShoppingCart.
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    serializer = RecipeShortListSerializer(recipe)
    if request.method == 'POST':
        if model.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                {'errors': 'Объект уже добавлен.'}
            )
        model.objects.create(
            user=request.user,
            recipe=recipe
        )
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED)
    to_delete = model.objects.filter(
        user=request.user,
        recipe=recipe
    )
    if to_delete.exists():
        to_delete.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
    raise serializers.ValidationError(
        {'errors': 'Остутствует объект удаления'}
    )


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
