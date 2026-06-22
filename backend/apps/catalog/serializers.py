from rest_framework import serializers
from .models import Category, Brand, Product, ProductVariant, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'is_active', 'children']

    def get_children(self, obj):
        active_children = obj.children.filter(is_active=True)
        return CategoryTreeSerializer(active_children, many=True).data


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductVariantSerializer(serializers.ModelSerializer):
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'sku', 'price', 'sale_price', 'effective_price', 'is_active']
        read_only_fields = ['id', 'effective_price']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'variant', 'image_url', 'sort_order']
        read_only_fields = ['id']


class ProductVariantWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    sku = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    sale_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )


class ProductListSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(
        source='brand.name', read_only=True, allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'specifications',
            'category', 'category_name', 'brand', 'brand_name',
            'is_active', 'created_at', 'variants', 'images',
        ]
        read_only_fields = ['id', 'created_at', 'category_name', 'brand_name']


class ProductWriteSerializer(serializers.ModelSerializer):
    variants = ProductVariantWriteSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'specifications',
            'category', 'brand', 'is_active', 'variants',
        ]

    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        product = Product.objects.create(**validated_data)
        for v in variants_data:
            ProductVariant.objects.create(product=product, **v)
        return product
