from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Min, Q
from apps.tenants.models import Store
from .models import Category, Brand, Product, ProductVariant
from .permissions import IsStoreOwner
from .serializers import (
    CategorySerializer, CategoryTreeSerializer, BrandSerializer,
    ProductListSerializer, ProductWriteSerializer, ProductVariantSerializer,
)


def get_store_for_request(request) -> Store | None:
    """Resolve tenant: from JWT if authenticated, else single active store."""
    if request.auth:
        tenant_id = request.auth.get('tenant_id')
        if tenant_id:
            return Store.objects.filter(id=tenant_id).first()
    return Store.objects.filter(is_active=True).first()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStoreOwner]

    def get_queryset(self):
        store = get_store_for_request(self.request)
        if not store:
            return Category.objects.none()
        return Category.objects.filter(tenant=store, is_active=True)

    def perform_create(self, serializer):
        store = get_store_for_request(self.request)
        serializer.save(tenant=store)

    def list(self, request, *args, **kwargs):
        if request.query_params.get('view') == 'tree':
            store = get_store_for_request(request)
            if not store:
                return Response([])
            roots = Category.objects.filter(
                tenant=store, parent__isnull=True, is_active=True
            )
            return Response(CategoryTreeSerializer(roots, many=True).data)
        return super().list(request, *args, **kwargs)


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsStoreOwner]

    def get_queryset(self):
        store = get_store_for_request(self.request)
        if not store:
            return Brand.objects.none()
        return Brand.objects.filter(tenant=store, is_active=True)

    def perform_create(self, serializer):
        store = get_store_for_request(self.request)
        serializer.save(tenant=store)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsStoreOwner]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'PUT'):
            return ProductWriteSerializer
        return ProductListSerializer

    def get_queryset(self):
        store = get_store_for_request(self.request)
        if not store:
            return Product.objects.none()
        qs = (
            Product.objects.filter(tenant=store, is_active=True)
            .select_related('category', 'brand')
            .prefetch_related('variants', 'images')
            .annotate(min_price=Min('variants__price'))
        )
        params = self.request.query_params

        category_slug = params.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        brand_slug = params.get('brand')
        if brand_slug:
            qs = qs.filter(brand__slug=brand_slug)

        search = params.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

        try:
            min_price = params.get('min_price')
            if min_price:
                qs = qs.filter(min_price__gte=float(min_price))
        except (ValueError, TypeError):
            pass

        try:
            max_price = params.get('max_price')
            if max_price:
                qs = qs.filter(min_price__lte=float(max_price))
        except (ValueError, TypeError):
            pass

        if params.get('in_stock') == 'true':
            qs = qs.filter(variants__inventory__available_qty__gt=0).distinct()

        sort = params.get('sort')
        if sort == 'price_asc':
            qs = qs.order_by('min_price')
        elif sort == 'price_desc':
            qs = qs.order_by('-min_price')
        else:
            qs = qs.order_by('-created_at')

        return qs

    def perform_create(self, serializer):
        store = get_store_for_request(self.request)
        serializer.save(tenant=store)

    @action(detail=True, methods=['get'], url_path='variants')
    def variants(self, request, slug=None):
        store = get_store_for_request(request)
        product = get_object_or_404(Product, slug=slug, tenant=store)
        active_variants = product.variants.filter(is_active=True)
        return Response(ProductVariantSerializer(active_variants, many=True).data)
