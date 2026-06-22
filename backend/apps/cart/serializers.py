from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    product_slug = serializers.CharField(source='variant.product.slug', read_only=True)
    price = serializers.DecimalField(source='variant.effective_price', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'variant_name', 'product_name', 'product_slug', 'qty', 'price', 'subtotal']
        read_only_fields = ['id', 'variant', 'variant_name', 'product_name', 'product_slug', 'price', 'subtotal']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total']
        read_only_fields = ['id']

    def get_total(self, obj):
        return sum(item.subtotal for item in obj.items.all())
