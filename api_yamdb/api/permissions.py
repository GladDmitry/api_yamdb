from rest_framework import permissions

MESSAGE_NO_PERMISSION = "У вас нет прав для выполнения этого действия."


class IsAuthenticatedAdminOrStaff(permissions.BasePermission):
    """
    Разрешение, которое предоставляет доступ
    только аутентифицированным пользователям,
    которые являются администраторами или суперпользователями.
    """
    message = MESSAGE_NO_PERMISSION

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsAuthenticatedAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет администраторам выполнять любые действия,
    а обычным пользователям — только чтение.
    """
    message = MESSAGE_NO_PERMISSION

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated and request.user.is_admin))


class IsAuthAdminModeratorAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет администраторам, модераторам и авторам
    выполнять любые действия, а обычным пользователям — только чтение.
    """
    message = MESSAGE_NO_PERMISSION

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_admin
            or request.user.is_moderator
            or (obj.author == request.user)
        )


class IsAuthOwner(permissions.BasePermission):
    """
    Разрешение, которое позволяет получить доступ только
    владельцам.
    """
    message = MESSAGE_NO_PERMISSION

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.username == request.user.username
