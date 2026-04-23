from django.contrib.auth.models import User
from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="actor",
        write_only=True,
        allow_null=True,
        required=False,
    )
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_id",
            "actor_username",
            "action",
            "entity_type",
            "entity_id",
            "description",
            "ip_address",
            "metadata",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = ["id", "actor", "created_at", "updated_at", "deleted_at"]

    def validate_entity_type(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Entity type is required.")
        return cleaned

    def validate_entity_id(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Entity id is required.")
        return cleaned

    def validate_metadata(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Metadata must be a JSON object.")
        return value
