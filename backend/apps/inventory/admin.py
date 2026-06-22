from django.contrib import admin
from .models import Inventory, InventoryMovement

admin.site.register(Inventory)
admin.site.register(InventoryMovement)
