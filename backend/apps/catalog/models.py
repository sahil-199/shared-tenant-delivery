from django.db import models
from django.utils.text import slugify
from apps.tenants.models import TenantModel


class Category(TenantModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    image = models.URLField(blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'categories'
        unique_together = ('tenant', 'slug')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(TenantModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    logo = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'slug')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TenantModel):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products'
    )
    brand = models.ForeignKey(
        Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name='products'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'slug')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    @property
    def effective_price(self):
        return self.sale_price if self.sale_price is not None else self.price

    def __str__(self):
        return f"{self.product.name} — {self.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(
        ProductVariant, null=True, blank=True, on_delete=models.SET_NULL, related_name='images'
    )
    image_url = models.URLField()
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']
