from rest_framework import viewsets

from accounts.permissions import IsAdminOrManager

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = AuditLog.objects.select_related('actor').filter(is_deleted=False)
	serializer_class = AuditLogSerializer
	permission_classes = [IsAdminOrManager]
	filterset_fields = ['action', 'entity_type', 'actor', 'is_deleted']
	search_fields = ['entity_type', 'entity_id', 'description', 'actor__username']
	ordering_fields = ['created_at', 'updated_at']
	ordering = ['-created_at']
