from rest_framework.permissions import BasePermission


class DenyByDefault(BasePermission):
    def has_permission(self, request, view):
        return False
