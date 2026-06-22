from django.contrib.postgres.fields import ArrayField
from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    logo = models.URLField(blank=True)
    delivery_pin_codes = ArrayField(
        models.CharField(max_length=10), default=list, blank=True
    )
    delivery_radius_km = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def is_pin_code_serviceable(self, pin_code: str) -> bool:
        return pin_code in self.delivery_pin_codes


class TenantModel(models.Model):
    tenant = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name='+'
    )

    class Meta:
        abstract = True
