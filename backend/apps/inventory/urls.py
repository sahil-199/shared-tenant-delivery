from rest_framework.routers import SimpleRouter
from .views import InventoryViewSet

router = SimpleRouter()
router.register('inventory', InventoryViewSet, basename='inventory')

urlpatterns = router.urls
