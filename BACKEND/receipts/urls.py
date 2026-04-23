from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReceiptViewSet

app_name = 'receipts'

router = DefaultRouter()
router.register(r'', ReceiptViewSet, basename='receipt')

urlpatterns = [
    path('', include(router.urls)),
]
