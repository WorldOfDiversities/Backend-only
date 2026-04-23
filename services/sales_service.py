"""Sales workflow service functions.

Step 6.2 will implement checkout orchestration here.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from accounts.models import UserProfile
from customers.models import Customer
from products.models import Product
from sales.models import Sale, SaleItem

from .errors import InventoryError, ValidationServiceError


@dataclass
class CheckoutRequest:
    cashier_profile_id: int
    customer_id: int | None
    items: list[dict]
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    notes: str = ""


@dataclass
class CheckoutResult:
    sale_id: int
    sale_number: str
    subtotal: Decimal
    total_amount: Decimal


def _normalize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _normalize_positive_int(value, field_name: str) -> int:
    try:
        quantity = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationServiceError(f"{field_name} must be a valid integer") from exc

    if quantity <= 0:
        raise ValidationServiceError(f"{field_name} must be greater than zero")

    return quantity


def _normalize_non_negative_money(value: Decimal, field_name: str) -> Decimal:
    normalized = Decimal(value)
    if normalized < 0:
        raise ValidationServiceError(f"{field_name} cannot be negative")
    return _normalize_money(normalized)


def checkout_sale(request: CheckoutRequest) -> CheckoutResult:
    """Create sale and sale items atomically.

    Implemented in Step 6.2.
    """
    if not request.items:
        raise ValidationServiceError("At least one item is required for checkout")

    discount_amount = _normalize_non_negative_money(request.discount_amount, "discount_amount")
    tax_amount = _normalize_non_negative_money(request.tax_amount, "tax_amount")

    cashier = UserProfile.objects.filter(id=request.cashier_profile_id, is_deleted=False).first()
    if cashier is None:
        raise ValidationServiceError("Cashier profile was not found")

    customer = None
    if request.customer_id is not None:
        customer = Customer.objects.filter(id=request.customer_id, is_deleted=False, is_active=True).first()
        if customer is None:
            raise ValidationServiceError("Customer was not found or is inactive")

    product_quantities: dict[int, int] = {}
    for index, item in enumerate(request.items, start=1):
        if not isinstance(item, dict):
            raise ValidationServiceError(f"items[{index}] must be an object")

        product_id = item.get("product_id")
        if product_id is None:
            raise ValidationServiceError(f"items[{index}] missing product_id")

        quantity = _normalize_positive_int(item.get("quantity"), f"items[{index}].quantity")
        product_quantities[int(product_id)] = product_quantities.get(int(product_id), 0) + quantity

    with transaction.atomic():
        products = {
            product.id: product
            for product in Product.objects.select_for_update()
            .filter(id__in=product_quantities.keys(), is_deleted=False, is_active=True)
        }

        missing_ids = [pid for pid in product_quantities.keys() if pid not in products]
        if missing_ids:
            raise ValidationServiceError(f"Products not found or inactive: {missing_ids}")

        subtotal = Decimal("0")
        for product_id, quantity in product_quantities.items():
            product = products[product_id]
            if quantity > product.quantity:
                raise InventoryError(
                    f"Insufficient stock for product '{product.name}'. Requested {quantity}, available {product.quantity}"
                )
            subtotal += _normalize_money(product.price) * quantity

        subtotal = _normalize_money(subtotal)
        total_amount = _normalize_money(subtotal - discount_amount + tax_amount)
        if total_amount < 0:
            raise ValidationServiceError("Final total cannot be negative")

        sale = Sale.objects.create(
            cashier=cashier,
            customer=customer,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=request.notes.strip(),
        )

        sale_items: list[SaleItem] = []
        for product_id, quantity in product_quantities.items():
            product = products[product_id]
            unit_price = _normalize_money(product.price)
            line_total = _normalize_money(unit_price * quantity)
            sale_items.append(
                SaleItem(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

        SaleItem.objects.bulk_create(sale_items)

    return CheckoutResult(
        sale_id=sale.id,
        sale_number=sale.sale_number,
        subtotal=sale.subtotal,
        total_amount=sale.total_amount,
    )
