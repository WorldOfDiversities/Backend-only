from django.db import models

from accounts.models import UserProfile
from common.models import BaseModel
from sales.models import Sale


class Payment(BaseModel):
	class Method(models.TextChoices):
		CASH = 'CASH', 'Cash'
		MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'
		CARD = 'CARD', 'Card'
		SPLIT = 'SPLIT', 'Split'

	class Status(models.TextChoices):
		PENDING = 'PENDING', 'Pending'
		COMPLETED = 'COMPLETED', 'Completed'
		FAILED = 'FAILED', 'Failed'
		REFUNDED = 'REFUNDED', 'Refunded'

	sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
	processed_by = models.ForeignKey(
		UserProfile,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='processed_payments',
	)
	method = models.CharField(max_length=20, choices=Method.choices)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	reference = models.CharField(max_length=120, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)

	class Meta:
		constraints = [
			models.CheckConstraint(condition=models.Q(amount__gt=0), name='payment_amount_gt_zero'),
		]

	def __str__(self):
		return f"{self.sale.sale_number} - {self.method} - {self.amount}"
