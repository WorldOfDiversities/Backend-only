from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

from common.models import BaseModel


class UserProfile(BaseModel):
	class Role(models.TextChoices):
		ADMIN = 'ADMIN', 'Admin'
		MANAGER = 'MANAGER', 'Manager'
		CASHIER = 'CASHIER', 'Cashier'

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
	phone_number = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return f"{self.user.username} ({self.role})"


class PasswordReset(BaseModel):
	"""
	Manages password reset tokens with expiry and one-time use tracking
	"""
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
	token = models.CharField(max_length=120, unique=True, default=uuid.uuid4)
	expires_at = models.DateTimeField()
	is_used = models.BooleanField(default=False)
	used_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Reset for {self.user.username} - {'Used' if self.is_used else 'Active'}"

	def is_expired(self):
		"""Check if token has expired"""
		return timezone.now() > self.expires_at

	def is_valid(self):
		"""Check if token is still valid (not expired and not used)"""
		return not self.is_expired() and not self.is_used

	def mark_as_used(self):
		"""Mark token as used"""
		self.is_used = True
		self.used_at = timezone.now()
		self.save()
