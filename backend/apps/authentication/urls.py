from django.urls import path

from .views import OTPRequestView, OTPVerifyView, TokenRefreshView

urlpatterns = [
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
