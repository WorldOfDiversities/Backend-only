from django.db import models


class TimeStampedModel(models.Model):
	"""Reusable created/updated audit fields."""

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class SoftDeleteModel(models.Model):
	"""Soft-delete support for records that should remain recoverable."""

	is_deleted = models.BooleanField(default=False)
	deleted_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		abstract = True


class BaseModel(TimeStampedModel, SoftDeleteModel):
	"""Project-wide base model combining audit and soft-delete fields."""

	class Meta:
		abstract = True


class SystemSettings(BaseModel):
	"""Singleton-style store/system settings payload for admin configuration."""

	key = models.CharField(max_length=32, unique=True, default="default")
	store_profile = models.JSONField(default=dict, blank=True)
	appearance = models.JSONField(default=dict, blank=True)
	regional = models.JSONField(default=dict, blank=True)
	pos = models.JSONField(default=dict, blank=True)
	receipt = models.JSONField(default=dict, blank=True)
	payment = models.JSONField(default=dict, blank=True)
	tax = models.JSONField(default=dict, blank=True)
	notifications = models.JSONField(default=dict, blank=True)
	security = models.JSONField(default=dict, blank=True)
	backup = models.JSONField(default=dict, blank=True)
	staff = models.JSONField(default=list, blank=True)

	class Meta:
		verbose_name = "System Settings"
		verbose_name_plural = "System Settings"

	def __str__(self):
		return f"Settings ({self.key})"
