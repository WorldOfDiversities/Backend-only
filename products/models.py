from django.db import models
from django.core.validators import MinValueValidator
import uuid

from common.models import BaseModel


def default_sku() -> str:
	return f"SKU-{uuid.uuid4().hex[:8].upper()}"


class Category(BaseModel):
	name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)

	def __str__(self):
		return self.name


class Supplier(BaseModel):
	name = models.CharField(max_length=150)
	phone_number = models.CharField(max_length=20, blank=True)
	email = models.EmailField(blank=True)
	address = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return self.name


class Product(BaseModel):
	sku = models.CharField(max_length=30, unique=True, default=default_sku)
	name = models.CharField(max_length=150)
	category = models.ForeignKey(
		Category,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='products',
	)
	supplier = models.ForeignKey(
		Supplier,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='products',
	)
	barcode = models.CharField(max_length=64, unique=True, null=True, blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	quantity = models.PositiveIntegerField(default=0)
	low_stock_threshold = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1)])
	is_active = models.BooleanField(default=True)

	@property
	def is_low_stock(self) -> bool:
		effective_threshold = max(self.low_stock_threshold, 1)
		return self.quantity <= effective_threshold

	def __str__(self):
		return f"{self.name} ({self.sku})"
