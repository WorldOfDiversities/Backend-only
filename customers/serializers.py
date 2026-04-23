from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "customer_code",
            "name",
            "phone_number",
            "email",
            "address",
            "loyalty_points",
            "is_active",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = ["id", "customer_code", "created_at", "updated_at", "deleted_at"]

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Customer name is required.")
        return cleaned
