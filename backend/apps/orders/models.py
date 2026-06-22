from django.db import models
from apps.tenants.models import TenantModel


class Address(TenantModel):
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='addresses')
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=6)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.line1}, {self.city} - {self.pin_code}"


class Order(TenantModel):
    PLACED = 'PLACED'
    PENDING_CONFIRMATION = 'PENDING_CONFIRMATION'
    CONFIRMED = 'CONFIRMED'
    PROCESSING = 'PROCESSING'
    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (PLACED, 'Placed'),
        (PENDING_CONFIRMATION, 'Pending Confirmation'),
        (CONFIRMED, 'Confirmed'),
        (PROCESSING, 'Processing'),
        (OUT_FOR_DELIVERY, 'Out for Delivery'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    ]

    # ponytail: simple forward-only transitions; add full state machine if edge cases arise
    VALID_TRANSITIONS = {
        PLACED: [PENDING_CONFIRMATION, CANCELLED],
        PENDING_CONFIRMATION: [CONFIRMED, CANCELLED],
        CONFIRMED: [PROCESSING, CANCELLED],
        PROCESSING: [OUT_FOR_DELIVERY, CANCELLED],
        OUT_FOR_DELIVERY: [DELIVERED],
        DELIVERED: [],
        CANCELLED: [],
    }

    user = models.ForeignKey('authentication.User', on_delete=models.PROTECT, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=PLACED)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey('catalog.ProductVariant', on_delete=models.PROTECT, related_name='order_items')
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    variant_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.variant_name} x{self.qty}"
