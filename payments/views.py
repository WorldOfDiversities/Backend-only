import json
import uuid
from decimal import Decimal
from urllib import error, request

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsStaffRole

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
	queryset = Payment.objects.select_related('sale', 'processed_by__user').filter(is_deleted=False)
	serializer_class = PaymentSerializer
	permission_classes = [IsStaffRole]
	filterset_fields = ['method', 'status', 'sale', 'processed_by', 'is_deleted']
	search_fields = ['sale__sale_number', 'reference', 'processed_by__user__username']
	ordering_fields = ['created_at', 'updated_at', 'amount']
	ordering = ['-created_at']

	@staticmethod
	def _normalize_email(candidate: str) -> str:
		email = (candidate or '').strip().lower()
		if not email:
			return 'pos.test@example.com'
		try:
			validate_email(email)
			return email
		except ValidationError:
			return 'pos.test@example.com'

	def _paystack_request(self, method: str, endpoint: str, payload: dict | None = None):
		secret_key = settings.PAYSTACK_SECRET_KEY
		if not secret_key:
			return None, 'PAYSTACK_SECRET_KEY is not configured.'

		url = f"{settings.PAYSTACK_BASE_URL.rstrip('/')}{endpoint}"
		body = None
		headers = {
			'Authorization': f'Bearer {secret_key}',
			'Content-Type': 'application/json',
			'Accept': 'application/json',
			'User-Agent': 'SwiftPOS-Server/1.0 (+https://localhost)',
		}
		if payload is not None:
			body = json.dumps(payload).encode('utf-8')

		try:
			req = request.Request(url, data=body, headers=headers, method=method.upper())
			with request.urlopen(req, timeout=30) as response:
				response_body = response.read().decode('utf-8')
				return json.loads(response_body), None
		except error.HTTPError as exc:
			raw_body = exc.read().decode('utf-8') if hasattr(exc, 'read') else ''
			try:
				parsed = json.loads(raw_body) if raw_body else {}
				message = parsed.get('message') or parsed.get('detail') or f'Paystack error ({exc.code})'
			except json.JSONDecodeError:
				if 'blocked access based on browser' in raw_body.lower():
					message = (
						'Paystack blocked this request signature. '
						'Retry after disabling aggressive browser privacy shields/VPN, '
						'or use a different browser/network.'
					)
				else:
					message = raw_body or f'Paystack error ({exc.code})'
			return None, message
		except error.URLError as exc:
			return None, f'Unable to reach Paystack: {exc.reason}'

	@staticmethod
	def _parse_gateway_payment_method(value: str) -> str:
		candidate = str(value or '').strip().upper()
		if not candidate:
			return Payment.Method.MOBILE_MONEY
		if candidate not in {Payment.Method.MOBILE_MONEY, Payment.Method.CARD}:
			raise ValueError('payment_method must be MOBILE_MONEY or CARD.')
		return candidate

	@action(detail=False, methods=['post'], url_path='paystack/initialize', permission_classes=[IsStaffRole])
	def paystack_initialize(self, request):
		amount = request.data.get('amount')
		payment_method_raw = request.data.get('payment_method', Payment.Method.MOBILE_MONEY)
		email = self._normalize_email(str(request.data.get('email', '')))
		phone_number = str(request.data.get('phone_number', '')).strip()
		currency = str(request.data.get('currency', 'GHS')).strip().upper() or 'GHS'

		try:
			payment_method = self._parse_gateway_payment_method(str(payment_method_raw))
		except ValueError as exc:
			return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		reference_prefix = 'CARD' if payment_method == Payment.Method.CARD else 'MOMO'
		reference = str(request.data.get('reference', '')).strip() or f"{reference_prefix}-{uuid.uuid4().hex[:12].upper()}"

		if amount is None:
			return Response({'detail': 'Amount is required.'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			amount_decimal = Decimal(str(amount))
		except Exception:
			return Response({'detail': 'Amount must be a valid number.'}, status=status.HTTP_400_BAD_REQUEST)

		if amount_decimal <= 0:
			return Response({'detail': 'Amount must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

		amount_kobo = int((amount_decimal * Decimal('100')).quantize(Decimal('1')))
		channel = 'card' if payment_method == Payment.Method.CARD else 'mobile_money'

		payload = {
			'email': email,
			'amount': amount_kobo,
			'currency': currency,
			'reference': reference,
			'channels': [channel],
			'metadata': {
				'integration': 'swiftpos',
				'payment_method': payment_method,
				'phone_number': phone_number,
			},
		}

		gateway_response, gateway_error = self._paystack_request('POST', '/transaction/initialize', payload)
		if gateway_error:
			return Response({'detail': gateway_error}, status=status.HTTP_400_BAD_REQUEST)

		if not gateway_response or not gateway_response.get('status'):
			message = (gateway_response or {}).get('message') or 'Paystack initialization failed.'
			return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)

		data = gateway_response.get('data') or {}
		return Response(
			{
				'payment_method': payment_method,
				'channel': channel,
				'reference': data.get('reference', reference),
				'authorization_url': data.get('authorization_url', ''),
				'access_code': data.get('access_code', ''),
				'message': gateway_response.get('message', f'{payment_method.title()} payment initialized.'),
			},
			status=status.HTTP_200_OK,
		)

	@action(detail=False, methods=['post'], url_path='paystack/verify', permission_classes=[IsStaffRole])
	def paystack_verify(self, request):
		reference = str(request.data.get('reference', '')).strip()
		if not reference:
			return Response({'detail': 'Reference is required.'}, status=status.HTTP_400_BAD_REQUEST)

		gateway_response, gateway_error = self._paystack_request('GET', f'/transaction/verify/{reference}')
		if gateway_error:
			return Response({'detail': gateway_error}, status=status.HTTP_400_BAD_REQUEST)

		if not gateway_response or not gateway_response.get('status'):
			message = (gateway_response or {}).get('message') or 'Unable to verify Paystack transaction.'
			return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)

		data = gateway_response.get('data') or {}
		verified = data.get('status') == 'success'
		return Response(
			{
				'verified': verified,
				'reference': data.get('reference', reference),
				'gateway_status': data.get('status', ''),
				'amount': (Decimal(data.get('amount', 0)) / Decimal('100')) if data.get('amount') is not None else Decimal('0'),
				'currency': data.get('currency', 'GHS'),
				'channel': data.get('channel', ''),
				'message': gateway_response.get('message', 'Verification complete.'),
			},
			status=status.HTTP_200_OK,
		)
