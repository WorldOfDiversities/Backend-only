from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urlencode

from .models import UserProfile, PasswordReset
from .permissions import IsAdminRole
from .serializers import (
	RegistrationSerializer,
	RoleAwareTokenObtainPairSerializer,
	UserProfileSerializer,
	PasswordResetRequestSerializer,
	PasswordResetConfirmSerializer,
	PasswordResetTokenValidateSerializer,
)


class RoleAwareTokenObtainPairView(TokenObtainPairView):
	serializer_class = RoleAwareTokenObtainPairSerializer


class RegisterView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = RegistrationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.save()
		return Response(data, status=status.HTTP_201_CREATED)


class UserProfileViewSet(viewsets.ModelViewSet):
	queryset = UserProfile.objects.select_related('user').filter(is_deleted=False)
	serializer_class = UserProfileSerializer
	permission_classes = [IsAdminRole]
	filterset_fields = ['role', 'is_deleted']
	search_fields = ['user__username', 'user__email', 'phone_number']
	ordering_fields = ['created_at', 'updated_at', 'role']
	ordering = ['user__username']


class PasswordResetRequestView(APIView):
	"""
	Request a password reset token to be sent to email.
	POST /api/v1/auth/password-reset-request/
	Body: {"email": "user@example.com"}
	"""
	permission_classes = [AllowAny]

	@staticmethod
	def _build_reset_url(request, token: str) -> str:
		template = str(getattr(settings, "PASSWORD_RESET_URL_TEMPLATE", "") or "").strip()
		if template:
			return template.format(token=token)

		origin = str(request.headers.get("Origin", "") or "").strip().rstrip("/")
		frontend_url = str(getattr(settings, "FRONTEND_URL", "") or "").strip().rstrip("/")
		base_url = origin or frontend_url or request.build_absolute_uri("/").rstrip("/")
		return f"{base_url}/reset-password.html?{urlencode({'token': str(token)})}"

	def post(self, request):
		serializer = PasswordResetRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()

		# Create password reset token
		reset_token = PasswordReset.objects.create(
			user=user,
			expires_at=timezone.now() + timedelta(hours=24)
		)

		# Build reset link
		reset_url = self._build_reset_url(request, str(reset_token.token))

		app_name = getattr(settings, "APP_NAME", "SwiftPOS")
		support_email = str(getattr(settings, "SUPPORT_EMAIL", getattr(settings, "DEFAULT_FROM_EMAIL", "")) or "").strip()
		try:
			validate_email(support_email)
		except ValidationError:
			support_email = ""

		# Send email
		email_subject = f"Reset your {app_name} password"
		email_body = f"""Hello {user.first_name or user.username},

We received a request to reset your password for your {app_name} account.

Click the link below to reset your password:
{reset_url}

This link expires in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
{app_name} Team"""

		email_html = f"""
<!doctype html>
<html>
  <body style=\"margin:0;padding:0;background:#f5f7fb;font-family:Arial,sans-serif;color:#1f2533;\">
    <table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\" style=\"padding:24px 0;\">
      <tr>
        <td align=\"center\">
          <table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" width=\"560\" style=\"max-width:560px;background:#ffffff;border:1px solid #d8dde8;border-radius:12px;overflow:hidden;\">
            <tr>
              <td style=\"padding:20px 24px;background:#102a57;color:#ffffff;font-size:20px;font-weight:700;\">{app_name}</td>
            </tr>
            <tr>
              <td style=\"padding:24px;font-size:15px;line-height:1.6;\">
                <p style=\"margin:0 0 12px;\">Hello {user.first_name or user.username},</p>
                <p style=\"margin:0 0 12px;\">We received a request to reset your password for your {app_name} account.</p>
                <p style=\"margin:0 0 18px;\">Click the button below to reset your password:</p>
                <p style=\"margin:0 0 20px;\"><a href=\"{reset_url}\" style=\"display:inline-block;padding:11px 18px;background:#102a57;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;\">Reset Password</a></p>
                <p style=\"margin:0 0 8px;\">This link expires in <strong>24 hours</strong>.</p>
                <p style=\"margin:0 0 10px;\">If the button does not work, copy and paste this URL into your browser:</p>
                <p style=\"margin:0 0 12px;word-break:break-all;color:#334155;\">{reset_url}</p>
                <p style=\"margin:0;\">If you did not request this, you can safely ignore this email.</p>
              </td>
            </tr>
            <tr>
              <td style=\"padding:16px 24px;background:#f8fafc;color:#64748b;font-size:12px;line-height:1.5;\">
                Need help? Contact <a href=\"mailto:{support_email}\" style=\"color:#102a57;\">{support_email}</a>.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

		from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "")
		if "<" not in from_email:
			from_email = f"{app_name} <{from_email}>"

		try:
			message = EmailMultiAlternatives(
				subject=email_subject,
				body=email_body,
				from_email=from_email,
				to=[user.email],
				reply_to=[support_email] if support_email else None,
				headers={
					"X-Auto-Response-Suppress": "All",
				},
			)
			message.attach_alternative(email_html, "text/html")
			message.send(fail_silently=False)
		except Exception as e:
			return Response(
				{"error": f"Failed to send email: {str(e)}"},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

		return Response(
			{"message": "Password reset link sent to your email. Please check your inbox."},
			status=status.HTTP_200_OK
		)


class PasswordResetTokenValidateView(APIView):
	"""
	Validate a password reset token without actually resetting the password.
	GET /api/v1/auth/password-reset-validate/?token=abc123xyz
	"""
	permission_classes = [AllowAny]

	def get(self, request):
		token = request.query_params.get('token')
		if not token:
			return Response(
				{"error": "Token is required"},
				status=status.HTTP_400_BAD_REQUEST
			)

		serializer = PasswordResetTokenValidateSerializer(data={'token': token})
		if serializer.is_valid():
			try:
				reset_obj = PasswordReset.objects.get(token=token)
				return Response(
					{
						"valid": True,
						"email": reset_obj.user.email,
						"message": "Token is valid. You can now reset your password."
					},
					status=status.HTTP_200_OK
				)
			except PasswordReset.DoesNotExist:
				pass

		return Response(
			{
				"valid": False,
				"error": serializer.errors.get('token', ['Invalid or expired token'])[0]
			},
			status=status.HTTP_400_BAD_REQUEST
		)


class PasswordResetConfirmView(APIView):
	"""
	Confirm password reset with token and new password.
	POST /api/v1/auth/password-reset-confirm/
	Body: {"token": "abc123xyz", "new_password": "newpass123", "confirm_password": "newpass123"}
	"""
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = PasswordResetConfirmSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()

		return Response(
			{"message": "Password reset successfully. You can now login with your new password."},
			status=status.HTTP_200_OK
		)
