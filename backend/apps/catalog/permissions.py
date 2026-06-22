from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsStoreOwner(BasePermission):
    """
    Safe methods (GET/HEAD/OPTIONS) are public.
    Unsafe methods require is_store_owner=True in JWT.
    Always raises PermissionDenied (403) rather than returning False (401)
    for unauthenticated unsafe requests.
    """
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if not request.user or not request.user.is_authenticated:
            raise PermissionDenied()
        if not (request.auth and request.auth.get('is_store_owner')):
            raise PermissionDenied()
        return True
