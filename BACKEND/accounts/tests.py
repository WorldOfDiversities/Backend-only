from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile


class RoleAwareTokenTests(APITestCase):
	token_url = "/api/v1/auth/token/"

	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username="admin_login",
			password="TestPass@123",
		)
		UserProfile.objects.create(user=self.user, role=UserProfile.Role.ADMIN)

	def test_login_succeeds_when_selected_role_matches_profile_role(self):
		payload = {
			"username": "admin_login",
			"password": "TestPass@123",
			"role": UserProfile.Role.ADMIN,
		}

		response = self.client.post(self.token_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("access", response.data)
		self.assertIn("refresh", response.data)
		self.assertEqual(response.data.get("role"), UserProfile.Role.ADMIN)

	def test_login_fails_when_selected_role_does_not_match_profile_role(self):
		payload = {
			"username": "admin_login",
			"password": "TestPass@123",
			"role": UserProfile.Role.MANAGER,
		}

		response = self.client.post(self.token_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		detail = response.data.get("detail")
		self.assertIsInstance(detail, list)
		self.assertEqual(str(detail[0]), "Incorrect role selected.")


@override_settings(
	EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
	DEFAULT_FROM_EMAIL="SwiftPOS <noreply@swiftpos.test>",
	APP_NAME="SwiftPOS",
	SUPPORT_EMAIL="support@swiftpos.test",
	FRONTEND_URL="http://127.0.0.1:5500",
)
class PasswordResetEmailTests(APITestCase):
	request_url = "/api/v1/auth/password-reset-request/"

	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username="reset_user",
			email="reset_user@example.com",
			password="ResetPass@123",
			first_name="Reset",
		)
		UserProfile.objects.create(user=self.user, role=UserProfile.Role.CASHIER)

	def test_password_reset_request_sends_multipart_email(self):
		response = self.client.post(
			self.request_url,
			{"email": self.user.email},
			format="json",
			HTTP_ORIGIN="https://pos.example.com",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(mail.outbox), 1)

		message = mail.outbox[0]
		self.assertEqual(message.to, [self.user.email])
		self.assertIn("Reset your SwiftPOS password", message.subject)
		self.assertIn("https://pos.example.com/reset-password.html?token=", message.body)
		self.assertEqual(message.reply_to, ["support@swiftpos.test"])
		self.assertGreaterEqual(len(message.alternatives), 1)
		self.assertEqual(message.alternatives[0].mimetype, "text/html")
