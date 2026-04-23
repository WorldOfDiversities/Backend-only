from rest_framework import viewsets

from accounts.permissions import IsStaffRole

from .models import Receipt
from .serializers import ReceiptSerializer


class ReceiptViewSet(viewsets.ModelViewSet):
	queryset = Receipt.objects.select_related('sale', 'payment').filter(is_deleted=False)
	serializer_class = ReceiptSerializer
	permission_classes = [IsStaffRole]
	filterset_fields = ['sale', 'payment', 'is_deleted']
	search_fields = ['receipt_number', 'store_name', 'sale__sale_number']
	ordering_fields = ['created_at', 'updated_at']
	ordering = ['-created_at']
