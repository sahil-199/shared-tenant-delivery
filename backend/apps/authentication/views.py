from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tenants.models import Store

from .models import CustomerProfile, OTPVerification, User
from .serializers import OTPRequestSerializer, OTPVerifySerializer
from .services import (
    AccountLocked,
    OTPRateLimitService,
    RateLimitExceeded,
    generate_otp,
    hash_otp,
    send_otp,
)
from .tokens import TenantRefreshToken


class OTPRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']

        rate_service = OTPRateLimitService()
        try:
            rate_service.check_rate_limit(phone)
            rate_service.check_lockout(phone)
        except RateLimitExceeded as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except AccountLocked as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp = generate_otp()
        otp_hash = hash_otp(otp)
        expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        OTPVerification.objects.create(phone=phone, otp_hash=otp_hash, expires_at=expires_at)
        rate_service.record_otp_request(phone)
        send_otp(phone, otp)

        return Response({'message': 'OTP sent successfully.'})


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        otp = serializer.validated_data['otp']
        otp_record = serializer.validated_data['otp_record']

        rate_service = OTPRateLimitService()

        # Lockout check BEFORE hash verification
        try:
            rate_service.check_lockout(phone)
        except AccountLocked as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # OTP hash check — record failure in Redis if wrong
        from .services import verify_otp_hash
        if not verify_otp_hash(otp, otp_record.otp_hash):
            rate_service.record_failed_attempt(phone)
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Success path
        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])
        rate_service.clear_failed_attempts(phone)

        # Get or create user
        user, is_new = User.objects.get_or_create(phone=phone)

        # Resolve store — single store for now
        store = Store.objects.filter(is_active=True).first()
        if not store:
            return Response({'error': 'No active store found.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Create profile if new
        if is_new:
            CustomerProfile.objects.get_or_create(user=user, tenant=store)

        refresh = TenantRefreshToken.for_user_and_store(user, store)

        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'is_new_user': is_new,
        })


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            return Response({'access': str(refresh.access_token)})
        except (TokenError, InvalidToken) as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
