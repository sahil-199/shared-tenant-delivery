from django.contrib import admin
from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'phone', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
