from rest_framework import serializers

from accounts.models import UserProfile
from products.models import Product

from .models import InventoryAlert, StockMovement


class StockMovementSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )
    performed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source="performed_by",
        write_only=True,
        allow_null=True,
        required=False,
    )
    product_name = serializers.CharField(source="product.name", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.user.username", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "product_id",
            "product_name",
            "movement_type",
            "quantity",
            "note",
            "performed_by",
            "performed_by_id",
            "performed_by_name",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "product",
            "performed_by",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def validate_quantity(self, value: int) -> int:
        if value == 0:
            raise serializers.ValidationError("Quantity cannot be zero.")
        return value


class InventoryAlertSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )
    resolved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source="resolved_by",
        write_only=True,
        allow_null=True,
        required=False,
    )
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = InventoryAlert
        fields = [
            "id",
            "product",
            "product_id",
            "product_name",
            "message",
            "is_resolved",
            "resolved_at",
            "resolved_by",
            "resolved_by_id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "product",
            "resolved_by",
            "resolved_at",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def validate_message(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Alert message is required.")
        return cleaned
