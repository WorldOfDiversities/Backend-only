from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminManagerOrReadOnly

from .models import Category, Product, Supplier
from .serializers import CategorySerializer, ProductSerializer, SupplierSerializer


class CategoryViewSet(viewsets.ModelViewSet):
	queryset = Category.objects.filter(is_deleted=False)
	serializer_class = CategorySerializer
	permission_classes = [IsAdminManagerOrReadOnly]
	search_fields = ['name', 'description']
	ordering_fields = ['name', 'created_at', 'updated_at']
	ordering = ['name']


class SupplierViewSet(viewsets.ModelViewSet):
	queryset = Supplier.objects.filter(is_deleted=False)
	serializer_class = SupplierSerializer
	permission_classes = [IsAdminManagerOrReadOnly]
	search_fields = ['name', 'email', 'phone_number']
	ordering_fields = ['name', 'created_at', 'updated_at']
	ordering = ['name']


class ProductViewSet(viewsets.ModelViewSet):
	queryset = Product.objects.select_related('category', 'supplier').filter(is_deleted=False)
	serializer_class = ProductSerializer
	permission_classes = [IsAdminManagerOrReadOnly]
	filterset_fields = ['category', 'supplier', 'is_active', 'is_deleted']
	search_fields = ['name', 'sku', 'barcode', 'category__name', 'supplier__name']
	ordering_fields = ['name', 'price', 'quantity', 'created_at', 'updated_at']
	ordering = ['name']

	@action(detail=False, methods=['get'], url_path='lookup-barcode', permission_classes=[IsAdminManagerOrReadOnly])
	def lookup_barcode(self, request):
		"""Look up a product by barcode. Returns product details if found."""
		barcode = request.query_params.get('barcode', '').strip()
		if not barcode:
			return Response(
				{'error': 'Barcode parameter is required.'},
				status=status.HTTP_400_BAD_REQUEST
			)

		try:
			product = Product.objects.select_related('category', 'supplier').get(
				barcode=barcode,
				is_deleted=False
			)
			serializer = self.get_serializer(product)
			return Response(serializer.data, status=status.HTTP_200_OK)
		except Product.DoesNotExist:
			return Response(
				{'error': f'No product found with barcode: {barcode}'},
				status=status.HTTP_404_NOT_FOUND
			)
