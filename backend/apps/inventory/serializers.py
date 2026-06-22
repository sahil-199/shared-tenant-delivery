from rest_framework import serializers
from .models import Inventory, InventoryMovement


class InventorySerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    sku = serializers.CharField(source='variant.sku', read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'variant', 'variant_name', 'product_name', 'sku',
            'available_qty', 'reserved_qty',
        ]
        read_only_fields = ['id', 'variant_name', 'product_name', 'sku']


class InventoryAdjustSerializer(serializers.Serializer):
    delta = serializers.IntegerField()
    reason = serializers.ChoiceField(choices=InventoryMovement.REASON_CHOICES)


class InventoryMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryMovement
        fields = ['id', 'inventory', 'delta', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']
