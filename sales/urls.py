from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SaleItemViewSet, SaleViewSet

app_name = 'sales'

router = DefaultRouter()
router.register(r'', SaleViewSet, basename='sale')
router.register(r'items', SaleItemViewSet, basename='sale-item')

urlpatterns = [
    path('', include(router.urls)),
]
