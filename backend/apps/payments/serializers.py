from rest_framework import serializers
from .models import Payment


class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    method = serializers.ChoiceField(choices=['cod', 'razorpay'])


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'method', 'status', 'razorpay_order_id', 'amount', 'created_at']
        read_only_fields = fields
