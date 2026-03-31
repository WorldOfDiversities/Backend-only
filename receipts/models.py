from django.db import models
import uuid

from common.models import BaseModel
from payments.models import Payment
from sales.models import Sale


def default_receipt_number() -> str:
	return f"RCP-{uuid.uuid4().hex[:10].upper()}"


class Receipt(BaseModel):
	sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='receipt')
	payment = models.ForeignKey(
		Payment,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='receipts',
	)
	receipt_number = models.CharField(max_length=32, unique=True, default=default_receipt_number)
	store_name = models.CharField(max_length=150, default='POS Store')
	payload = models.JSONField(default=dict, blank=True)

	def __str__(self):
		return self.receipt_number
