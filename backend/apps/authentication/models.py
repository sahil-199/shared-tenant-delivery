from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True)
    is_store_owner = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone


class CustomerProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    tenant = models.ForeignKey('tenants.Store', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tenant')

    def __str__(self):
        return f"{self.user.phone} @ {self.tenant.name}"


class OTPVerification(models.Model):
    phone = models.CharField(max_length=15)
    otp_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['phone', 'created_at'])]

    def __str__(self):
        return f"OTP for {self.phone}"
