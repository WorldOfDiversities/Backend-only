from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsStaffRole
from services.checkout_service import CheckoutWorkflowRequest, process_checkout
from services.errors import ServiceError

from .models import Sale, SaleItem
from .serializers import (
	CheckoutRequestSerializer,
	CheckoutResponseSerializer,
	SaleItemSerializer,
	SaleSerializer,
)


class SaleViewSet(viewsets.ModelViewSet):
	queryset = Sale.objects.select_related('cashier__user', 'customer').filter(is_deleted=False)
	serializer_class = SaleSerializer
	permission_classes = [IsStaffRole]
	filterset_fields = ['status', 'cashier', 'customer', 'is_deleted']
	search_fields = ['sale_number', 'cashier__user__username', 'customer__name']
	ordering_fields = ['created_at', 'updated_at', 'subtotal', 'total_amount']
	ordering = ['-created_at']

	@action(detail=False, methods=['post'], url_path='checkout')
	def checkout(self, request):
		request_serializer = CheckoutRequestSerializer(data=request.data)
		request_serializer.is_valid(raise_exception=True)

		profile = getattr(request.user, 'profile', None)
		if profile is None:
			return Response(
				{'detail': 'Authenticated user does not have a cashier profile.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		validated = request_serializer.validated_data
		try:
			result = process_checkout(
				CheckoutWorkflowRequest(
					cashier_profile_id=profile.id,
					customer_id=validated.get('customer_id'),
					items=validated['items'],
					payment_method=validated['payment_method'],
					payment_reference=validated.get('payment_reference', ''),
					discount_amount=validated.get('discount_amount', 0),
					tax_amount=validated.get('tax_amount', 0),
					notes=validated.get('notes', ''),
				)
			)
		except ServiceError as exc:
			return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		response_serializer = CheckoutResponseSerializer(
			{
				'sale_id': result.sale_id,
				'sale_number': result.sale_number,
				'subtotal': result.subtotal,
				'total_amount': result.total_amount,
				'payment_id': result.payment_id,
				'receipt_id': result.receipt_id,
			}
		)
		return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class SaleItemViewSet(viewsets.ModelViewSet):
	queryset = SaleItem.objects.select_related('sale', 'product').filter(is_deleted=False)
	serializer_class = SaleItemSerializer
	permission_classes = [IsStaffRole]
	filterset_fields = ['sale', 'product', 'is_deleted']
	search_fields = ['sale__sale_number', 'product__name', 'product__sku']
	ordering_fields = ['created_at', 'updated_at', 'quantity', 'unit_price', 'line_total']
	ordering = ['-created_at']
