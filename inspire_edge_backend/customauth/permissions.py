from rest_framework.permissions import BasePermission
from .models import UserRole

from django.utils import timezone


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class HasRolePermission(BasePermission):
    def __init__(self, role_name):
        self.role_name = role_name

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                UserRole.objects.filter(user=request.user, role__name=self.role_name).exists())


class IsPremiumUser(BasePermission):
    """
    Allows access only to users with active premium subscription (Pro or Enterprise tier).
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Check if user has active subscription
        user = request.user
        now = timezone.now()

        # For trial users
        if user.trial_end and user.trial_end > now and not user.trial_used:
            return True

        # For paid subscribers
        if user.is_paid and user.subscription_end and user.subscription_end > now:
            return True

        # Check tier (Pro or Enterprise)
        if user.tier in ['pro', 'enterprise']:
            return True

        return False