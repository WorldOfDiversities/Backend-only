from django.contrib import admin

from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
	list_display = ("key", "updated_at", "created_at")
	search_fields = ("key",)
from django.contrib import admin

# Register your models here.
