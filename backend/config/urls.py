from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/', include('apps.tenants.urls')),
    path('api/v1/', include('apps.catalog.urls')),
    path('api/v1/', include('apps.inventory.urls')),
    path('api/v1/', include('apps.cart.urls')),
    path('api/v1/', include('apps.orders.urls')),
    path('api/v1/', include('apps.payments.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
