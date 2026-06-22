import hashlib
import hmac
import logging
import razorpay
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.catalog.views import get_store_for_request
from apps.orders.models import Order
from .models import Payment
from .serializers import PaymentInitiateSerializer, PaymentSerializer

logger = logging.getLogger(__name__)


class PaymentInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        ser = PaymentInitiateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        store = get_store_for_request(request)
        try:
            order = Order.objects.select_for_update().get(
                id=ser.validated_data['order_id'],
                tenant=store,
                user=request.user,
                status=Order.PLACED,
            )
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(order, 'payment'):
            return Response({'detail': 'Payment already initiated.'}, status=status.HTTP_400_BAD_REQUEST)

        method = ser.validated_data['method']
        payment = Payment(order=order, method=method, amount=order.total_amount, tenant=store)

        if method == 'cod':
            payment.status = 'paid'
            payment.save()
            order.status = Order.PENDING_CONFIRMATION
            order.save()
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

        # Razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        rp_order = client.order.create({
            'amount': int(order.total_amount * 100),  # paise
            'currency': 'INR',
            'receipt': f'order_{order.id}',
        })
        payment.razorpay_order_id = rp_order['id']
        payment.status = 'initiated'
        payment.save()
        data = PaymentSerializer(payment).data
        data['razorpay_key'] = settings.RAZORPAY_KEY_ID
        return Response(data, status=status.HTTP_201_CREATED)


class RazorpayWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        sig = request.headers.get('X-Razorpay-Signature', '')
        body = request.body
        expected = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            logger.warning(f'Razorpay webhook signature verification failed. Signature: {sig[:10]}...')
            return Response({'detail': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

        payload = request.data
        event = payload.get('event')
        if event == 'payment.captured':
            try:
                rp_payment_id = payload['payload']['payment']['entity']['id']
                rp_order_id = payload['payload']['payment']['entity']['order_id']
            except KeyError:
                logger.warning('Malformed Razorpay webhook payload: missing nested keys')
                return Response({'status': 'ok'})

            try:
                payment = Payment.objects.select_related('order').get(razorpay_order_id=rp_order_id)
                payment.razorpay_payment_id = rp_payment_id
                payment.status = 'paid'
                payment.save()
                payment.order.status = Order.PENDING_CONFIRMATION
                payment.order.save()
            except Payment.DoesNotExist:
                logger.error(f'Payment not found for Razorpay order ID: {rp_order_id}')
        return Response({'status': 'ok'})
