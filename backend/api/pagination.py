from rest_framework.pagination import PageNumberPagination


class MyPagination(PageNumberPagination):
    """Кастомный пагинатор на базе стандартного

    Переопределены поля 'page_size_query_param' для вывода указанного
    количества страниц, 'page_size' для определения размера страницы.

    """
    page_size_query_param = 'limit'
    page_size = 6
