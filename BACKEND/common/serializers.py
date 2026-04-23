from rest_framework import serializers

from .models import SystemSettings


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = [
            "id",
            "key",
            "store_profile",
            "appearance",
            "regional",
            "pos",
            "receipt",
            "payment",
            "tax",
            "notifications",
            "security",
            "backup",
            "staff",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "key", "created_at", "updated_at"]

    def validate(self, attrs):
        json_object_fields = [
            "store_profile",
            "appearance",
            "regional",
            "pos",
            "receipt",
            "payment",
            "tax",
            "notifications",
            "security",
            "backup",
        ]
        for field_name in json_object_fields:
            if field_name in attrs and not isinstance(attrs[field_name], dict):
                raise serializers.ValidationError({field_name: "Must be an object."})

        if "staff" in attrs and not isinstance(attrs["staff"], list):
            raise serializers.ValidationError({"staff": "Must be a list."})

        return attrs
