from rest_framework import serializers
from .models import Address, Order, OrderItem


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'line1', 'line2', 'city', 'state', 'pin_code', 'lat', 'lng', 'is_default']
        read_only_fields = ['id']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'variant', 'variant_name', 'qty', 'unit_price']
        read_only_fields = ['id', 'variant_name', 'unit_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    address = AddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'total_amount', 'notes', 'created_at', 'address', 'items']
        read_only_fields = ['id', 'status', 'total_amount', 'created_at']


class CheckoutSerializer(serializers.Serializer):
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
