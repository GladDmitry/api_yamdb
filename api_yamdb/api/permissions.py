from rest_framework import permissions

MESSAGE_NO_PERMISSION = "У вас нет прав для выполнения этого действия."


class IsAdminOrSuperUser(permissions.BasePermission):
    """
    Разрешение, которое позволяет доступ только администраторам.
    """
    message = MESSAGE_NO_PERMISSION

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return (request.user.is_admin
                    or request.user.is_superuser
                    or request.user.is_staff)
        return False


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет администраторам выполнять любые действия,
    а обычным пользователям — только чтение.
    """
    message = MESSAGE_NO_PERMISSION

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated and request.user.is_admin))


class IsAdminModeratorAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет администраторам, модераторам и авторам
    выполнять любые действия, а обычным пользователям — только чтение.
    """
    message = MESSAGE_NO_PERMISSION

    def has_permission(self, request, view):
        # Позволить анонимным пользователям доступ к GET-запросам
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_admin
            or request.user.is_moderator
            or (obj.author == request.user)
        )


class IsAuthenticatedUser (permissions.BasePermission):
    """
    Разрешение, которое позволяет доступ только
    аутентифицированным пользователям.
    """
    message = MESSAGE_NO_PERMISSION

    def has_permission(self, request, view):
        # Разрешить доступ только аутентифицированным пользователям
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешить доступ к объекту только для владельца
        return obj == request.user