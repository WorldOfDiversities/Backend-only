from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from inventory.models import StockMovement
from payments.models import Payment
from products.models import Category, Product
from receipts.models import Receipt
from sales.models import Sale


class CheckoutApiTests(APITestCase):
	checkout_url = "/api/v1/sales/checkout/"

	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username="test_cashier",
			password="TestPass@123",
			is_staff=True,
		)
		self.profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.CASHIER)

		self.category = Category.objects.create(name="Test Category")
		self.product = Product.objects.create(
			name="Checkout Product",
			category=self.category,
			price=Decimal("10.00"),
			quantity=20,
			low_stock_threshold=5,
		)

	def _auth(self):
		self.client.force_authenticate(user=self.user)

	def test_checkout_success_creates_sale_payment_receipt_and_stock_movement(self):
		self._auth()
		payload = {
			"items": [{"product_id": self.product.id, "quantity": 2}],
			"payment_method": "CASH",
			"discount_amount": "1.00",
			"tax_amount": "0.50",
			"notes": "test checkout",
		}

		response = self.client.post(self.checkout_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(Sale.objects.filter(id=response.data["sale_id"]).exists())
		self.assertTrue(Payment.objects.filter(id=response.data["payment_id"]).exists())
		self.assertTrue(Receipt.objects.filter(id=response.data["receipt_id"]).exists())
		self.assertEqual(
			StockMovement.objects.filter(
				movement_type=StockMovement.MovementType.SALE,
				note=f"Sale {response.data['sale_number']}",
			).count(),
			1,
		)

		self.product.refresh_from_db()
		self.assertEqual(self.product.quantity, 18)

	def test_checkout_fails_when_stock_is_insufficient(self):
		self._auth()
		payload = {
			"items": [{"product_id": self.product.id, "quantity": 999}],
			"payment_method": "CASH",
			"discount_amount": "0.00",
			"tax_amount": "0.00",
		}

		response = self.client.post(self.checkout_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertFalse(Sale.objects.exists())
		self.assertFalse(Payment.objects.exists())
		self.assertFalse(Receipt.objects.exists())

		self.product.refresh_from_db()
		self.assertEqual(self.product.quantity, 20)

	def test_checkout_fails_when_authenticated_user_has_no_profile(self):
		user_model = get_user_model()
		no_profile_user = user_model.objects.create_user(
			username="no_profile",
			password="TestPass@123",
		)
		self.client.force_authenticate(user=no_profile_user)

		payload = {
			"items": [{"product_id": self.product.id, "quantity": 1}],
			"payment_method": "CASH",
			"discount_amount": "0.00",
			"tax_amount": "0.00",
		}

		response = self.client.post(self.checkout_url, payload, format="json")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertIn("detail", response.data)

	def test_checkout_card_payment_succeeds_with_reference(self):
		self._auth()
		payload = {
			"items": [{"product_id": self.product.id, "quantity": 1}],
			"payment_method": "CARD",
			"payment_reference": "CARD-TXN-001",
			"discount_amount": "0.00",
			"tax_amount": "0.00",
		}

		response = self.client.post(self.checkout_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		payment = Payment.objects.get(id=response.data["payment_id"])
		self.assertEqual(payment.method, Payment.Method.CARD)
		self.assertEqual(payment.reference, "CARD-TXN-001")
