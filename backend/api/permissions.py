from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Кастомный класс разрешения.

    Разрешает создание/изменение/удаление обьекта только автору
    или служебному персоналу. Для остальных только чтение.

    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            obj.author == request.user
            or request.user.is_staff
            or request.method in permissions.SAFE_METHODS
        )


class IsCreateOrReadOnly(permissions.BasePermission):
    """Кастомный класс разрешения.

    Разрешает создание обьекта только анонимным пользователям.
    Для остальных только чтение.

    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.method == 'POST' and request.user.is_anonymous)
        )

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Кастомный класс разрешения.

    Разрешает создание/изменение/удаление обьекта только служебному персоналу.
    Для остальных только чтение.

    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_staff
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_staff
        )
