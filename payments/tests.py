from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile


class PaystackInitializeApiTests(APITestCase):
	url = "/api/v1/payments/paystack/initialize/"

	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username="payments_user",
			password="TestPass@123",
			is_staff=True,
		)
		self.profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.CASHIER)
		self.client.force_authenticate(self.user)

	@patch("payments.views.PaymentViewSet._paystack_request")
	def test_paystack_initialize_card_uses_card_channel(self, mock_gateway_request):
		mock_gateway_request.return_value = (
			{
				"status": True,
				"message": "Authorization URL created",
				"data": {
					"reference": "CARD-ABC123",
					"authorization_url": "https://paystack.test/authorize",
					"access_code": "ACCESS123",
				},
			},
			None,
		)

		payload = {
			"amount": "25.50",
			"email": "customer@example.com",
			"payment_method": "CARD",
			"currency": "GHS",
		}

		response = self.client.post(self.url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["payment_method"], "CARD")
		self.assertEqual(response.data["channel"], "card")
		self.assertEqual(response.data["reference"], "CARD-ABC123")

		call_args, _ = mock_gateway_request.call_args
		sent_payload = call_args[2]
		self.assertEqual(sent_payload["channels"], ["card"])
		self.assertEqual(sent_payload["metadata"]["payment_method"], "CARD")
		self.assertEqual(sent_payload["amount"], 2550)

	@patch("payments.views.PaymentViewSet._paystack_request")
	def test_paystack_initialize_defaults_to_mobile_money(self, mock_gateway_request):
		mock_gateway_request.return_value = (
			{
				"status": True,
				"message": "Authorization URL created",
				"data": {
					"reference": "MOMO-XYZ123",
					"authorization_url": "https://paystack.test/authorize",
					"access_code": "ACCESS456",
				},
			},
			None,
		)

		response = self.client.post(self.url, {"amount": Decimal("10.00")}, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["payment_method"], "MOBILE_MONEY")
		self.assertEqual(response.data["channel"], "mobile_money")

		call_args, _ = mock_gateway_request.call_args
		sent_payload = call_args[2]
		self.assertEqual(sent_payload["channels"], ["mobile_money"])
		self.assertEqual(sent_payload["metadata"]["payment_method"], "MOBILE_MONEY")

	def test_paystack_initialize_rejects_unsupported_payment_method(self):
		response = self.client.post(
			self.url,
			{"amount": "10.00", "payment_method": "BANK_TRANSFER"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("payment_method", response.data["detail"])
