from django.db import models
import uuid

from accounts.models import UserProfile
from common.models import BaseModel
from customers.models import Customer
from products.models import Product


def default_sale_number() -> str:
	return f"SAL-{uuid.uuid4().hex[:10].upper()}"


class Sale(BaseModel):
	class Status(models.TextChoices):
		COMPLETED = 'COMPLETED', 'Completed'
		CANCELLED = 'CANCELLED', 'Cancelled'
		REFUNDED = 'REFUNDED', 'Refunded'

	sale_number = models.CharField(max_length=32, unique=True, default=default_sale_number)
	cashier = models.ForeignKey(
		UserProfile,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='sales',
	)
	customer = models.ForeignKey(
		Customer,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='sales',
	)
	subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.sale_number


class SaleItem(BaseModel):
	sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
	quantity = models.PositiveIntegerField(default=1)
	unit_price = models.DecimalField(max_digits=12, decimal_places=2)
	line_total = models.DecimalField(max_digits=12, decimal_places=2)

	class Meta:
		constraints = [
			models.CheckConstraint(condition=models.Q(quantity__gt=0), name='sale_item_quantity_gt_zero'),
		]

	def save(self, *args, **kwargs):
		self.line_total = self.quantity * self.unit_price
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.sale.sale_number} - {self.product.name}"
