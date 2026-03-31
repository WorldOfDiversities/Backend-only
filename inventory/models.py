from django.db import models
from django.utils import timezone

from accounts.models import UserProfile
from common.models import BaseModel
from products.models import Product


class StockMovement(BaseModel):
	class MovementType(models.TextChoices):
		SALE = 'SALE', 'Sale'
		RESTOCK = 'RESTOCK', 'Restock'
		ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
		RETURN = 'RETURN', 'Return'

	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
	movement_type = models.CharField(max_length=20, choices=MovementType.choices)
	quantity = models.IntegerField()
	note = models.CharField(max_length=255, blank=True)
	performed_by = models.ForeignKey(
		UserProfile,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='inventory_actions',
	)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.product.name} | {self.movement_type} | {self.quantity}"


class InventoryAlert(BaseModel):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_alerts')
	message = models.CharField(max_length=255)
	is_resolved = models.BooleanField(default=False)
	resolved_at = models.DateTimeField(null=True, blank=True)
	resolved_by = models.ForeignKey(
		UserProfile,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='resolved_inventory_alerts',
	)

	def mark_resolved(self, user_profile: UserProfile | None = None):
		self.is_resolved = True
		self.resolved_at = timezone.now()
		self.resolved_by = user_profile
		self.save(update_fields=['is_resolved', 'resolved_at', 'resolved_by', 'updated_at'])

	def __str__(self):
		return f"Alert: {self.product.name}"
