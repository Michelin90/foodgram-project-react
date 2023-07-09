from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import CustomUser, Subscribe

from .core.views_utils import (create_and_download_file,
                               get_paginated_queryset, post_delete_object)
from .filters import IngredientFilterSet, RecipeFilterSet
from .pagination import MyPagination
from .permissions import (IsAdminOrReadOnly, IsCreateOrReadOnly,
                          IsOwnerOrReadOnly)
from .serializers import (IngredientSerializer, RecipeCerateSerializer,
                          RecipeReadSerializer, SetPasswordSerializer,
                          SubscribeSerializer, TagSerialzer,
                          UserCreateSerializer, UserReadSerialzer)

from reportlab.pdfgen import canvas


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с запросами к модели CustomUser."""

    queryset = CustomUser.objects.all().order_by('id')
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
        """Возвращающает профиль текущего пользователя.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            Response: Текущий пользователь.

        """
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
        """Меняет пароль текущего пользователя.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            Response: Cтатус подтверждающий или запрещающий выбранное действие.

        """
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
        """Оформляет или отменяет подписку на выбранного автора.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): id автора, на которого офоромляется
                или отменяется подписка.

        Retrurns:
            Response: Cтатус подтверждающий или запрещающий выбранное действие.

        """
        subscribing = get_object_or_404(CustomUser, pk=pk)
        serializer = SubscribeSerializer(
            subscribing,
            data=request.data,
            context={'request': request}
        )
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(
                user=request.user,
                subscribing=subscribing
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        Subscribe.objects.filter(
            user=request.user,
            subscribing=subscribing
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        permission_classes=(permissions.IsAuthenticated,),
        detail=False
    )
    def subscriptions(self, request):
        """Возвращает список авторов, на которых осуществлена подписка.

        Args:
            request (HttpResponse): Объект запроса.

        Returns:
            Response : Ответ, содержащий автров из списка подписок.

        """
        subscribtions = CustomUser.objects.filter(
            subscribing__user=request.user
        )
        return get_paginated_queryset(
            self, SubscribeSerializer, subscribtions, request
        )


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с запросами к модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerialzer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с запросами к модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet


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
        """Добавяет или удаляет выбранный рецепт в избранном.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): id рецепта, удаляемого или добавляемого избранном.

        Returns:
            Response: Cтатус подтверждающий или запрещающий выбранное действие.

        """
        return post_delete_object(request, pk, Favorite)

    @action(
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
        url_path='favorite'
    )
    def favorite_list(self, request,):
        """Возвращает рецепты из списка избранного текущего пользователя.

        Args:
            request (HttpResponse): Объект запроса.

        Returns:
            Response : Ответ, содержащий рецепты из списка избранного.

        """
        favorites = Recipe.objects.filter(favorite__user=request.user)
        filtered_queryset = self.filter_queryset(favorites)
        return get_paginated_queryset(
            self, RecipeReadSerializer, filtered_queryset, request
        )

    @action(
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,),
        detail=True
    )
    def shopping_cart(self, request, pk=None):
        """Добавяет или удаляет выбранный рецепт в списке покупок.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): id рецепта, удаляемого или добавляемого в список покупок.

        Returns:
            Response: Cтатус подтверждающий или запрещающий выбранное действие.

        """
        return post_delete_object(request, pk, ShoppingCart)

    @action(
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
        url_path='shopping_cart'
    )
    def shopping_cart_list(self, request):
        """Возвращает рецепты из списка покупок текущего пользователя.

        Args:
            request (HttpResponse): Объект запроса.

        Returns:
            Response : Ответ, содержащий рецепты из списка покупок.

        """
        shopping_cart = Recipe.objects.filter(shopping_cart__user=request.user)
        return get_paginated_queryset(
            self, RecipeReadSerializer, shopping_cart, request
        )

    @action(
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
    )
    def download_shopping_cart(self, request):
        """Скачивает файл со списком покупок.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            response (HttpResponse): Ответ с файлом.

        """
        user = request.user
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="file.pdf"'
        page = canvas.Canvas(response)
        create_and_download_file(user, page)
        return response
