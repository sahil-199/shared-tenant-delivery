from decimal import Decimal
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from apps.catalog.permissions import IsStoreOwner
from apps.catalog.views import get_store_for_request
from apps.cart.models import Cart, CartItem
from apps.inventory.models import Inventory
from apps.notifications.services import send_whatsapp
from .models import Address, Order, OrderItem
from .serializers import AddressSerializer, OrderSerializer, CheckoutSerializer, OrderStatusSerializer


class AddressListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        store = get_store_for_request(self.request)
        return Address.objects.filter(user=self.request.user, tenant=store)

    def perform_create(self, serializer):
        store = get_store_for_request(self.request)
        serializer.save(user=self.request.user, tenant=store)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        store = get_store_for_request(request)
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        address = serializer.validated_data['address']
        if address.pin_code not in store.delivery_pin_codes:
            raise ValidationError({'detail': 'Delivery not available to this pin code.'})

        cart = get_object_or_404(Cart, user=request.user, tenant=store)
        items = list(CartItem.objects.filter(cart=cart).select_related('variant'))
        if not items:
            raise ValidationError({'detail': 'Cart is empty.'})

        total = Decimal('0')
        order_items = []
        for ci in items:
            variant = ci.variant
            inv, _ = Inventory.objects.get_or_create(
                variant=variant,
                defaults={'tenant': store, 'available_qty': 0, 'reserved_qty': 0}
            )
            if inv.available_qty < ci.qty:
                raise ValidationError({'detail': f'{variant.product.name} ({variant.name}) is out of stock.'})
            price = variant.effective_price
            total += price * ci.qty
            order_items.append((ci, variant, price))

        order = Order.objects.create(
            tenant=store, user=request.user, address=address,
            status=Order.PLACED, total_amount=total,
            notes=serializer.validated_data.get('notes', '')
        )

        for ci, variant, price in order_items:
            OrderItem.objects.create(
                order=order, variant=variant, qty=ci.qty,
                unit_price=price, variant_name=variant.name
            )
            inv = Inventory.objects.get(variant=variant, tenant=store)
            inv.adjust(delta=-ci.qty, reason='RESERVE')

        cart.items.all().delete()

        send_whatsapp(
            request.user.phone, 'order_placed',
            {'order_id': order.id, 'total': str(total)}
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store = get_store_for_request(request)
        if request.auth and request.auth.get('is_store_owner'):
            orders = Order.objects.filter(tenant=store).prefetch_related('items')
        else:
            orders = Order.objects.filter(tenant=store, user=request.user).prefetch_related('items')
        return Response(OrderSerializer(orders, many=True).data)


class OrderDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        store = get_store_for_request(self.request)
        if self.request.auth and self.request.auth.get('is_store_owner'):
            return Order.objects.filter(tenant=store)
        return Order.objects.filter(tenant=store, user=self.request.user)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsStoreOwner]

    def patch(self, request, pk):
        if not (request.auth and request.auth.get('is_store_owner')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        store = get_store_for_request(request)
        order = get_object_or_404(Order, pk=pk, tenant=store)
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']
        if new_status not in Order.VALID_TRANSITIONS.get(order.status, []):
            raise ValidationError({'detail': f'Cannot transition from {order.status} to {new_status}.'})
        order.status = new_status
        order.save()
        return Response(OrderSerializer(order).data)
