from rest_framework import permissions


class IsAdminOrStaff(permissions.BasePermission):
    pass


class IsAdminUserOrReadOnly(permissions.BasePermission):
    pass


class IsAdminModeratorAuthorOrReadOnly(permissions.BasePermission):
    pass
