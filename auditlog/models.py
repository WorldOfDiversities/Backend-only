from django.db import models
from django.contrib.auth.models import User

from common.models import BaseModel


class AuditLog(BaseModel):
	class Action(models.TextChoices):
		CREATE = 'CREATE', 'Create'
		UPDATE = 'UPDATE', 'Update'
		DELETE = 'DELETE', 'Delete'
		LOGIN = 'LOGIN', 'Login'
		LOGOUT = 'LOGOUT', 'Logout'
		SALE = 'SALE', 'Sale'
		PAYMENT = 'PAYMENT', 'Payment'
		STOCK_ADJUSTMENT = 'STOCK_ADJUSTMENT', 'Stock Adjustment'

	actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
	action = models.CharField(max_length=32, choices=Action.choices)
	entity_type = models.CharField(max_length=80)
	entity_id = models.CharField(max_length=64)
	description = models.TextField(blank=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	metadata = models.JSONField(default=dict, blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.action} {self.entity_type}({self.entity_id})"
