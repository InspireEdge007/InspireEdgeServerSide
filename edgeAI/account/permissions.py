from rest_framework.permissions import BasePermission
from .models import UserRole

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class HasRolePermission(BasePermission):
    def __init__(self, role_name):
        self.role_name = role_name

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                UserRole.objects.filter(user=request.user, role__name=self.role_name).exists())