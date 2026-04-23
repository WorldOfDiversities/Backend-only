from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InventoryAlertViewSet, StockMovementViewSet

app_name = 'inventory'

router = DefaultRouter()
router.register(r'movements', StockMovementViewSet, basename='stock-movement')
router.register(r'alerts', InventoryAlertViewSet, basename='inventory-alert')

urlpatterns = [
    path('', include(router.urls)),
]
