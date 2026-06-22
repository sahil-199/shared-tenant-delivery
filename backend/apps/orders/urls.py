from django.urls import path
from .views import AddressListCreateView, CheckoutView, OrderListView, OrderDetailView, OrderStatusUpdateView

urlpatterns = [
    path('addresses/', AddressListCreateView.as_view(), name='addresses'),
    path('orders/', CheckoutView.as_view(), name='checkout'),
    path('orders/list/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status'),
]
