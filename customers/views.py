from rest_framework import viewsets

from accounts.permissions import IsStaffRole

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
	queryset = Customer.objects.filter(is_deleted=False)
	serializer_class = CustomerSerializer
	permission_classes = [IsStaffRole]
	filterset_fields = ['is_active', 'is_deleted']
	search_fields = ['name', 'customer_code', 'phone_number', 'email']
	ordering_fields = ['name', 'loyalty_points', 'created_at', 'updated_at']
	ordering = ['name']
