"""Checkout workflow orchestration service.

Step 6.6 coordinates sale creation, stock deduction, payment finalization,
and receipt generation in one transaction boundary.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from .errors import OrchestrationError, ServiceError
from .inventory_service import apply_sale_stock_deduction
from .payment_service import finalize_payment
from .receipt_service import generate_receipt_for_sale
from .sales_service import CheckoutRequest, checkout_sale


@dataclass
class CheckoutWorkflowRequest:
    cashier_profile_id: int
    customer_id: int | None
    items: list[dict]
    payment_method: str
    payment_reference: str = ""
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    notes: str = ""


@dataclass
class CheckoutWorkflowResult:
    sale_id: int
    sale_number: str
    subtotal: Decimal
    total_amount: Decimal
    payment_id: int
    receipt_id: int


def process_checkout(request: CheckoutWorkflowRequest) -> CheckoutWorkflowResult:
    """Process end-to-end checkout with rollback on any failure."""
    try:
        with transaction.atomic():
            sale_result = checkout_sale(
                CheckoutRequest(
                    cashier_profile_id=request.cashier_profile_id,
                    customer_id=request.customer_id,
                    items=request.items,
                    discount_amount=request.discount_amount,
                    tax_amount=request.tax_amount,
                    notes=request.notes,
                )
            )

            apply_sale_stock_deduction(sale_result.sale_id)

            payment_id = finalize_payment(
                sale_id=sale_result.sale_id,
                processed_by_profile_id=request.cashier_profile_id,
                method=request.payment_method,
                amount=sale_result.total_amount,
                reference=request.payment_reference,
            )

            receipt_id = generate_receipt_for_sale(
                sale_id=sale_result.sale_id,
                payment_id=payment_id,
            )

            return CheckoutWorkflowResult(
                sale_id=sale_result.sale_id,
                sale_number=sale_result.sale_number,
                subtotal=sale_result.subtotal,
                total_amount=sale_result.total_amount,
                payment_id=payment_id,
                receipt_id=receipt_id,
            )
    except ServiceError:
        raise
    except Exception as exc:
        raise OrchestrationError(f"Checkout workflow failed: {exc}") from exc
