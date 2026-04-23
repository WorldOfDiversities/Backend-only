"""Receipt workflow service functions.

Step 6.5 will implement receipt payload generation here.
"""

from decimal import Decimal

from django.db import transaction

from payments.models import Payment
from receipts.models import Receipt
from sales.models import Sale

from .errors import ValidationServiceError


def _money(value: Decimal) -> str:
    return str(Decimal(value).quantize(Decimal("0.01")))


def _build_payload(*, sale: Sale, payment: Payment | None) -> dict:
    items_payload = []
    for item in sale.items.select_related('product').filter(is_deleted=False):
        items_payload.append(
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "sku": item.product.sku,
                "quantity": item.quantity,
                "unit_price": _money(item.unit_price),
                "line_total": _money(item.line_total),
            }
        )

    return {
        "sale": {
            "sale_id": sale.id,
            "sale_number": sale.sale_number,
            "created_at": sale.created_at.isoformat(),
            "status": sale.status,
            "notes": sale.notes,
        },
        "cashier": {
            "profile_id": sale.cashier_id,
            "username": sale.cashier.user.username if sale.cashier else None,
        },
        "customer": {
            "customer_id": sale.customer_id,
            "name": sale.customer.name if sale.customer else None,
        },
        "totals": {
            "subtotal": _money(sale.subtotal),
            "discount_amount": _money(sale.discount_amount),
            "tax_amount": _money(sale.tax_amount),
            "total_amount": _money(sale.total_amount),
        },
        "items": items_payload,
        "payment": {
            "payment_id": payment.id if payment else None,
            "method": payment.method if payment else None,
            "amount": _money(payment.amount) if payment else None,
            "status": payment.status if payment else None,
            "reference": payment.reference if payment else None,
        },
    }


def generate_receipt_for_sale(*, sale_id: int, payment_id: int | None = None) -> int:
    """Build and store receipt payload for a sale.

    Returns created or updated receipt id.
    """
    sale = (
        Sale.objects.select_related('cashier__user', 'customer')
        .filter(id=sale_id, is_deleted=False)
        .first()
    )
    if sale is None:
        raise ValidationServiceError("Sale was not found")

    payment = None
    if payment_id is not None:
        payment = Payment.objects.filter(id=payment_id, is_deleted=False).first()
        if payment is None:
            raise ValidationServiceError("Payment was not found")
        if payment.sale_id != sale.id:
            raise ValidationServiceError("Payment does not belong to the provided sale")

    payload = _build_payload(sale=sale, payment=payment)

    with transaction.atomic():
        receipt, _created = Receipt.objects.update_or_create(
            sale=sale,
            defaults={
                'payment': payment,
                'store_name': 'POS Store',
                'payload': payload,
            },
        )

    return receipt.id
