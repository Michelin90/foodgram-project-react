from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe, Tag
from users.models import CustomUser

STATUS_CHOICES = (
    ('1', 'True'),
    ('0', 'False'),
)


class RecipeFilterSet(FilterSet):
    """Набор фильтров для запросов к модели Recipe."""
    author = filters.ModelChoiceFilter(
        queryset=CustomUser.objects.all()
    )
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )
    is_favorited = filters.ChoiceFilter(
        method='get_is_favorited',
        choices=STATUS_CHOICES
    )
    is_in_shopping_cart = filters.ChoiceFilter(
        method='get_is_in_shopping_cart',
        choices=STATUS_CHOICES)

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
        )

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value in STATUS_CHOICES[0]:
            return queryset.filter(favorite__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value in STATUS_CHOICES[0]:
            return queryset.filter(shopping_cart__user=user)
        return queryset
