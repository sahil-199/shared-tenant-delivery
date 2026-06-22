from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.catalog.permissions import IsStoreOwner
from apps.catalog.views import get_store_for_request
from apps.catalog.models import ProductVariant
from .models import Inventory, InventoryMovement
from .serializers import (
    InventorySerializer, InventoryAdjustSerializer, InventoryMovementSerializer
)


def _require_owner(request):
    if not (request.auth and request.auth.get('is_store_owner')):
        raise PermissionDenied()


class InventoryViewSet(viewsets.ViewSet):
    permission_classes = [IsStoreOwner]

    def list(self, request):
        _require_owner(request)
        store = get_store_for_request(request)
        inventories = (
            Inventory.objects.filter(tenant=store)
            .select_related('variant__product')
        )
        return Response(InventorySerializer(inventories, many=True).data)

    def partial_update(self, request, pk=None):
        _require_owner(request)
        store = get_store_for_request(request)
        variant = get_object_or_404(ProductVariant, pk=pk, product__tenant=store)
        inventory, _ = Inventory.objects.get_or_create(
            variant=variant,
            defaults={'tenant': store, 'available_qty': 0, 'reserved_qty': 0},
        )
        serializer = InventoryAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory.adjust(
            delta=serializer.validated_data['delta'],
            reason=serializer.validated_data['reason'],
        )
        inventory.refresh_from_db()
        return Response(InventorySerializer(inventory).data)

    @action(detail=False, methods=['get'])
    def movements(self, request):
        _require_owner(request)
        store = get_store_for_request(request)
        movements = InventoryMovement.objects.filter(
            inventory__tenant=store
        ).select_related('inventory')
        return Response(InventoryMovementSerializer(movements, many=True).data)
