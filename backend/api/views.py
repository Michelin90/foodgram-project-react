from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import CustomUser, Subscribe

from .filters import RecipeFilterSet
from .pagination import MyPagination
from .permissions import (IsAdminOrReadOnly, IsCreateOrReadOnly,
                          IsOwnerOrReadOnly)
from .serializers import (IngredientSerializer, RecipeCerateSerializer,
                          RecipeReadSerializer, SetPasswordSerializer,
                          SubscribeSerializer, TagSerialzer,
                          UserCreateSerializer, UserReadSerialzer)
from .utils import get_paginated_qeryset, post_delete_object


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с запросами к модели CustomUser."""
    queryset = CustomUser.objects.all()
    permission_classes = (IsCreateOrReadOnly,)
    pagination_class = MyPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerialzer
        return UserCreateSerializer

    @action(
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def me(self, request):
        """Метод, возвращающий профиль текущего пользователя."""
        serializer = UserReadSerialzer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post'],
        permission_classes=(permissions.IsAuthenticated,),
        detail=False
    )
    def set_password(self, request):
        """Метод. позволяющий сменить пароль текущего пользователя."""
        serializer = SetPasswordSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        permission_classes=(permissions.IsAuthenticated,),
        detail=True
    )
    def subscribe(self, request, pk=None):
        """
        Метод, позволяющий оформить или отменить
        текущему пользователю подписку на выбранного автора.
        """
        subscribing = get_object_or_404(CustomUser, pk=pk)
        serializer = SubscribeSerializer(
            subscribing,
            context={'request': request})
        if request.method == 'POST':
            if Subscribe.objects.filter(
                user=request.user,
                subscribing=subscribing
            ).exists():
                raise serializers.ValidationError(
                    {'errors': 'Подписка на этого автора уже оформлена.'}
                )
            if request.user == subscribing:
                raise serializers.ValidationError(
                    {'errors': 'Нельзя подписаться на самого себя.'}
                )
            Subscribe.objects.create(
                user=request.user,
                subscribing=subscribing
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        to_delete = Subscribe.objects.filter(
            user=request.user,
            subscribing=subscribing
        )
        if to_delete.exists():
            to_delete.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise serializers.ValidationError(
            {'errors': 'Подписка на этого автора не осуществлена'}
        )

    @action(
        permission_classes=(permissions.IsAuthenticated,),
        detail=False
    )
    def subscribtions(self, request,):
        """
        Метод, возвращающий список обьектов авторов, на которых у
        текущего пользователя оформлена подписка.
        """
        subscribtions = CustomUser.objects.filter(
            subscribing__user=request.user
        )
        return get_paginated_qeryset(
            self, SubscribeSerializer, subscribtions, request
        )


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с запросами к модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerialzer
    permission_classes = (IsAdminOrReadOnly,)


class IngridientViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с запросами к модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с запросами к модели Recipe."""
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeCerateSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    @action(
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,),
        detail=True
    )
    def favorite(self, request, pk=None):
        """
        Метод, добавляющий или удаляющий выбранный рецепт
        в списке избранного текущего пользователя.
        """
        return post_delete_object(request, pk, Favorite)

    @action(
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
        url_path='favorite'
    )
    def favorite_list(self, request,):
        """
        Метод, возвращающий список обьектов рецептов, которые
        находятся в списке избранного текущего пользователя.
        """
        favorites = Recipe.objects.filter(favorite__user=request.user)
        filtered_queryset = self.filter_queryset(favorites)
        return get_paginated_qeryset(
            self, RecipeReadSerializer, filtered_queryset, request
        )

    @action(
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,),
        detail=True
    )
    def shopping_cart(self, request, pk=None):
        """
        Метод, добавляющий или удаляющий выбранный рецепт
        в списке покупок текущего пользователя.
        """
        return post_delete_object(request, pk, ShoppingCart)

    @action(
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
        url_path='shopping_cart'
    )
    def shopping_cart_list(self, request,):
        """
        Метод, возвращающий список обьектов рецептов, которые
        находятся в списке покупок текущего пользователя.
        """
        shopping_cart = Recipe.objects.filter(shopping_cart__user=request.user)
        return get_paginated_qeryset(
            self, RecipeReadSerializer, shopping_cart, request
        )

    @action(
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
    )
    def download_shopping_cart(self, request):
        """
        Метод, возвращающий текстовый документ, содержащий
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
