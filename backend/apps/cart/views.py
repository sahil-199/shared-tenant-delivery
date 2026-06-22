from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView, DestroyAPIView
from django.shortcuts import get_object_or_404
from apps.catalog.views import get_store_for_request
from apps.catalog.models import ProductVariant
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store = get_store_for_request(request)
        cart, _ = Cart.objects.get_or_create(
            user=request.user, tenant=store,
        )
        return Response(CartSerializer(cart).data)


class CartItemAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        store = get_store_for_request(request)
        variant_id = request.data.get('variant')
        qty = int(request.data.get('qty', 1))
        variant = get_object_or_404(ProductVariant, pk=variant_id, product__tenant=store)
        cart, _ = Cart.objects.get_or_create(user=request.user, tenant=store)
        item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={'qty': 0})
        item.qty += qty
        item.save()
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class CartItemUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        store = get_store_for_request(self.request)
        return CartItem.objects.filter(cart__user=self.request.user, cart__tenant=store)


class CartItemDeleteView(DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        store = get_store_for_request(self.request)
        return CartItem.objects.filter(cart__user=self.request.user, cart__tenant=store)
