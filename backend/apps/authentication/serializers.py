import re
from django.utils import timezone
from rest_framework import serializers
from .models import OTPVerification


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        # Indian mobile numbers: 10 digits, starting with 6-9
        cleaned = re.sub(r'[\s\-\+]', '', value)
        if not re.match(r'^[6-9]\d{9}$', cleaned):
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return cleaned


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_phone(self, value):
        cleaned = re.sub(r'[\s\-\+]', '', value)
        if not re.match(r'^[6-9]\d{9}$', cleaned):
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return cleaned

    def validate(self, data):
        phone = data['phone']

        record = (
            OTPVerification.objects
            .filter(phone=phone, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if not record:
            raise serializers.ValidationError({"otp": "No OTP found for this number. Request a new one."})

        if record.expires_at < timezone.now():
            raise serializers.ValidationError({"otp": "OTP has expired. Request a new one."})

        data['otp_record'] = record
        return data
