from django.db import models, transaction
from apps.tenants.models import TenantModel


class Inventory(TenantModel):
    variant = models.OneToOneField(
        'catalog.ProductVariant', on_delete=models.CASCADE, related_name='inventory'
    )
    available_qty = models.IntegerField(default=0)
    reserved_qty = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'inventories'

    def adjust(self, delta: int, reason: str) -> 'InventoryMovement':
        with transaction.atomic():
            self.available_qty += delta
            self.save(update_fields=['available_qty'])
            return InventoryMovement.objects.create(
                inventory=self, delta=delta, reason=reason
            )

    def __str__(self):
        return f"{self.variant} — qty: {self.available_qty}"


class InventoryMovement(models.Model):
    RESTOCK = 'RESTOCK'
    RESERVE = 'RESERVE'
    RELEASE = 'RELEASE'
    SELL = 'SELL'
    ADJUSTMENT = 'ADJUSTMENT'

    REASON_CHOICES = [
        (RESTOCK, 'Restock'),
        (RESERVE, 'Reserve'),
        (RELEASE, 'Release'),
        (SELL, 'Sell'),
        (ADJUSTMENT, 'Adjustment'),
    ]

    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name='movements'
    )
    delta = models.IntegerField()
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
