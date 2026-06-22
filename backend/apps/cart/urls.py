from django.urls import path
from .views import CartView, CartItemAddView, CartItemUpdateView, CartItemDeleteView

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/items/', CartItemAddView.as_view(), name='cart-item-add'),
    path('cart/items/<int:pk>/', CartItemUpdateView.as_view(), name='cart-item-update'),
    path('cart/items/<int:pk>/delete/', CartItemDeleteView.as_view(), name='cart-item-delete'),
]
