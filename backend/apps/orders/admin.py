from django.contrib import admin
from .models import Address, Order, OrderItem

admin.site.register(Address)
admin.site.register(Order)
admin.site.register(OrderItem)
