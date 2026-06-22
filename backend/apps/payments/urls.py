from django.urls import path
from .views import PaymentInitiateView, RazorpayWebhookView

urlpatterns = [
    path('payments/initiate/', PaymentInitiateView.as_view()),
    path('payments/webhook/razorpay/', RazorpayWebhookView.as_view()),
]
