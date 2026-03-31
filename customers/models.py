from django.db import models
import uuid

from common.models import BaseModel


def default_customer_code() -> str:
	return f"CUS-{uuid.uuid4().hex[:8].upper()}"


class Customer(BaseModel):
	customer_code = models.CharField(max_length=30, unique=True, default=default_customer_code)
	name = models.CharField(max_length=150)
	phone_number = models.CharField(max_length=20, blank=True)
	email = models.EmailField(blank=True)
	address = models.CharField(max_length=255, blank=True)
	loyalty_points = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return f"{self.name} ({self.customer_code})"
