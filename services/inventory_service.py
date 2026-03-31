"""Inventory workflow service functions.

Step 6.3 will implement stock deduction and alert creation here.
"""

from django.db import transaction

from inventory.models import InventoryAlert, StockMovement
from products.models import Product
from sales.models import Sale, SaleItem

from .errors import InventoryError, ValidationServiceError


def apply_sale_stock_deduction(sale_id: int) -> None:
    """Deduct inventory based on sale items and record stock movements.

    Idempotency guard: if sale stock movements already exist for this sale note,
    this function does nothing.
    """
    sale = Sale.objects.select_related('cashier').filter(id=sale_id, is_deleted=False).first()
    if sale is None:
        raise ValidationServiceError("Sale was not found")

    sale_items = list(
        SaleItem.objects.select_related('product')
        .filter(sale_id=sale.id, is_deleted=False)
    )
    if not sale_items:
        raise ValidationServiceError("Sale has no items to deduct from inventory")

    movement_note = f"Sale {sale.sale_number}"
    existing_movements = StockMovement.objects.filter(
        movement_type=StockMovement.MovementType.SALE,
        note=movement_note,
        is_deleted=False,
    ).exists()
    if existing_movements:
        return

    quantity_by_product: dict[int, int] = {}
    for item in sale_items:
        quantity_by_product[item.product_id] = quantity_by_product.get(item.product_id, 0) + item.quantity

    with transaction.atomic():
        products = {
            product.id: product
            for product in Product.objects.select_for_update().filter(id__in=quantity_by_product.keys())
        }

        missing_ids = [pid for pid in quantity_by_product.keys() if pid not in products]
        if missing_ids:
            raise InventoryError(f"Products missing for stock deduction: {missing_ids}")

        movement_rows: list[StockMovement] = []
        low_stock_alerts: list[InventoryAlert] = []

        for product_id, deduction_qty in quantity_by_product.items():
            product = products[product_id]
            if deduction_qty > product.quantity:
                raise InventoryError(
                    f"Insufficient stock for '{product.name}'. Requested {deduction_qty}, available {product.quantity}"
                )

            product.quantity -= deduction_qty
            product.save(update_fields=['quantity', 'updated_at'])

            movement_rows.append(
                StockMovement(
                    product=product,
                    movement_type=StockMovement.MovementType.SALE,
                    quantity=-deduction_qty,
                    note=movement_note,
                    performed_by=sale.cashier,
                )
            )

            low_stock_exists = InventoryAlert.objects.filter(
                product=product,
                is_resolved=False,
                is_deleted=False,
            ).exists()
            if product.quantity <= product.low_stock_threshold and not low_stock_exists:
                low_stock_alerts.append(
                    InventoryAlert(
                        product=product,
                        message=(
                            f"Low stock for {product.name}. "
                            f"Current quantity: {product.quantity}, threshold: {product.low_stock_threshold}"
                        ),
                    )
                )

        StockMovement.objects.bulk_create(movement_rows)
        if low_stock_alerts:
            InventoryAlert.objects.bulk_create(low_stock_alerts)
