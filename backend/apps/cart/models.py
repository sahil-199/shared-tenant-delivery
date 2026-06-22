from decimal import Decimal
from django.db import models
from apps.tenants.models import TenantModel


class Cart(TenantModel):
    user = models.ForeignKey(
        'authentication.User', on_delete=models.CASCADE, related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'user')

    def __str__(self):
        return f"Cart({self.user}, {self.tenant})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(
        'catalog.ProductVariant', on_delete=models.CASCADE, related_name='cart_items'
    )
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'variant')

    @property
    def subtotal(self) -> Decimal:
        return self.variant.effective_price * self.qty

    def __str__(self):
        return f"{self.variant} x{self.qty}"
