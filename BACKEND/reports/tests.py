from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from payments.models import Payment
from products.models import Category, Product
from sales.models import Sale, SaleItem


class ReportApiTests(APITestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username="report_manager",
			password="TestPass@123",
		)
		self.profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.MANAGER)

		self.category = Category.objects.create(name="Beverages")
		self.low_stock_product = Product.objects.create(
			name="Low Stock Cola",
			category=self.category,
			price=Decimal("6.50"),
			quantity=2,
			low_stock_threshold=5,
		)
		self.normal_product = Product.objects.create(
			name="Normal Stock Juice",
			category=self.category,
			price=Decimal("8.00"),
			quantity=20,
			low_stock_threshold=5,
		)

		sale = Sale.objects.create(
			cashier=self.profile,
			subtotal=Decimal("13.00"),
			discount_amount=Decimal("0.00"),
			tax_amount=Decimal("0.00"),
			total_amount=Decimal("13.00"),
			status=Sale.Status.COMPLETED,
		)
		SaleItem.objects.create(sale=sale, product=self.low_stock_product, quantity=2, unit_price=Decimal("6.50"), line_total=Decimal("13.00"))
		Payment.objects.create(sale=sale, processed_by=self.profile, method=Payment.Method.CASH, amount=Decimal("13.00"), status=Payment.Status.COMPLETED)

	def _auth(self):
		self.client.force_authenticate(user=self.user)

	def test_reports_require_authentication(self):
		response = self.client.get("/api/v1/reports/sales/daily/")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_daily_sales_report_returns_aggregates(self):
		self._auth()
		response = self.client.get("/api/v1/reports/sales/daily/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("daily", response.data)
		self.assertIn("payment_breakdown", response.data)
		self.assertGreaterEqual(len(response.data["daily"]), 1)

	def test_inventory_summary_report_flags_low_stock_products(self):
		self._auth()
		response = self.client.get("/api/v1/reports/inventory/summary/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("summary", response.data)
		self.assertIn("low_stock", response.data)
		low_stock_names = [row["name"] for row in response.data["low_stock"]]
		self.assertIn("Low Stock Cola", low_stock_names)
		self.assertNotIn("Normal Stock Juice", low_stock_names)

	def test_inventory_summary_excludes_soft_deleted_products(self):
		deleted_low_stock = Product.objects.create(
			name="Deleted Low Stock",
			category=self.category,
			price=Decimal("4.00"),
			quantity=1,
			low_stock_threshold=5,
			is_deleted=True,
		)

		self._auth()
		response = self.client.get("/api/v1/reports/inventory/summary/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		low_stock_names = [row["name"] for row in response.data["low_stock"]]
		self.assertNotIn(deleted_low_stock.name, low_stock_names)

		summary = response.data["summary"]
		self.assertEqual(summary["total_products"], 2)
		self.assertEqual(summary["active_products"], 2)
