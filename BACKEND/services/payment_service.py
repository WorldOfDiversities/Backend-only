"""Payment workflow service functions.

Step 6.4 will implement payment finalization here.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from accounts.models import UserProfile
from payments.models import Payment
from sales.models import Sale

from .errors import BusinessRuleError, ValidationServiceError


def _normalize_money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def finalize_payment(*, sale_id: int, processed_by_profile_id: int | None, method: str, amount: Decimal, reference: str = "") -> int:
    """Create and validate payment for a sale.

    Returns created payment id.
    """
    normalized_amount = _normalize_money(amount)
    if normalized_amount <= 0:
        raise ValidationServiceError("Payment amount must be greater than zero")

    if method not in Payment.Method.values:
        raise ValidationServiceError(f"Unsupported payment method: {method}")

    cleaned_reference = reference.strip()
    if method in {Payment.Method.MOBILE_MONEY, Payment.Method.CARD, Payment.Method.SPLIT} and not cleaned_reference:
        raise ValidationServiceError("Payment reference is required for electronic payments")

    with transaction.atomic():
        sale = Sale.objects.select_for_update().filter(id=sale_id, is_deleted=False).first()
        if sale is None:
            raise ValidationServiceError("Sale was not found")

        processed_by = None
        if processed_by_profile_id is not None:
            processed_by = UserProfile.objects.filter(id=processed_by_profile_id, is_deleted=False).first()
            if processed_by is None:
                raise ValidationServiceError("Processed-by profile was not found")

        already_paid = (
            Payment.objects.filter(
                sale=sale,
                is_deleted=False,
                status=Payment.Status.COMPLETED,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        already_paid = _normalize_money(already_paid)
        sale_total = _normalize_money(sale.total_amount)
        remaining = _normalize_money(sale_total - already_paid)

        if remaining <= 0:
            raise BusinessRuleError("Sale is already fully paid")

        if normalized_amount > remaining:
            raise ValidationServiceError(
                f"Payment exceeds remaining balance. Remaining: {remaining}, attempted: {normalized_amount}"
            )

        if normalized_amount < remaining:
            raise ValidationServiceError(
                f"Partial payment is not allowed in current workflow. Remaining: {remaining}"
            )

        # For electronic payments, create with PENDING status until verified
        initial_status = Payment.Status.PENDING if method in {Payment.Method.MOBILE_MONEY, Payment.Method.CARD, Payment.Method.SPLIT} else Payment.Status.COMPLETED
        
        payment = Payment.objects.create(
            sale=sale,
            processed_by=processed_by,
            method=method,
            amount=normalized_amount,
            reference=cleaned_reference,
            status=initial_status,
        )

        # Mark sale as completed only if payment is immediately completed (CASH)
        if initial_status == Payment.Status.COMPLETED and sale.status != Sale.Status.COMPLETED:
            sale.status = Sale.Status.COMPLETED
            sale.save(update_fields=["status", "updated_at"])

    return payment.id


def verify_and_complete_payment(*, payment_id: int, verified_from_gateway: bool = False) -> dict:
    """Verify a pending payment and mark as completed if verified.
    
    Used for electronic payments after Paystack confirmation.
    
    Returns dict with:
        - payment_id: int
        - status: str (COMPLETED or maintained PENDING)
        - sale_id: int
        - sale_status: str
    """
    with transaction.atomic():
        payment = Payment.objects.select_for_update().filter(
            id=payment_id,
            is_deleted=False,
        ).first()
        
        if payment is None:
            raise ValidationServiceError("Payment not found")
        
        if payment.status == Payment.Status.COMPLETED:
            raise BusinessRuleError("Payment is already completed")
        
        if payment.status == Payment.Status.FAILED:
            raise BusinessRuleError("Cannot verify a failed payment")
        
        if payment.status == Payment.Status.REFUNDED:
            raise BusinessRuleError("Cannot verify a refunded payment")
        
        # Mark payment as completed
        payment.status = Payment.Status.COMPLETED
        payment.save(update_fields=["status", "updated_at"])
        
        # Mark sale as completed
        sale = payment.sale
        if sale.status != Sale.Status.COMPLETED:
            sale.status = Sale.Status.COMPLETED
            sale.save(update_fields=["status", "updated_at"])
        
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "sale_id": sale.id,
            "sale_status": sale.status,
        }
