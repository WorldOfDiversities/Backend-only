from rest_framework import viewsets

from accounts.permissions import IsAdminManagerOrReadOnly, IsStaffRole

from .models import InventoryAlert, StockMovement
from .serializers import InventoryAlertSerializer, StockMovementSerializer


class StockMovementViewSet(viewsets.ModelViewSet):
	queryset = StockMovement.objects.select_related('product', 'performed_by__user').filter(is_deleted=False)
	serializer_class = StockMovementSerializer
	permission_classes = [IsStaffRole]
	filterset_fields = ['movement_type', 'product', 'performed_by', 'is_deleted']
	search_fields = ['product__name', 'product__sku', 'note', 'performed_by__user__username']
	ordering_fields = ['created_at', 'updated_at', 'quantity']
	ordering = ['-created_at']


class InventoryAlertViewSet(viewsets.ModelViewSet):
	queryset = InventoryAlert.objects.select_related('product', 'resolved_by__user').filter(is_deleted=False)
	serializer_class = InventoryAlertSerializer
	permission_classes = [IsAdminManagerOrReadOnly]
	filterset_fields = ['product', 'is_resolved', 'resolved_by', 'is_deleted']
	search_fields = ['product__name', 'message']
	ordering_fields = ['created_at', 'updated_at', 'resolved_at']
	ordering = ['-created_at']
