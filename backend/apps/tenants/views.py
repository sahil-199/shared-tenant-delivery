from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Store
from .serializers import StoreSerializer


class IsStoreOwner(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.auth and request.auth.get('is_store_owner', False)


class StoreView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsStoreOwner()]

    def get(self, request):
        store = Store.objects.filter(is_active=True).first()
        if not store:
            return Response({'error': 'Store not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StoreSerializer(store).data)

    def patch(self, request):
        store = Store.objects.get(id=request.auth['tenant_id'])
        serializer = StoreSerializer(store, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
