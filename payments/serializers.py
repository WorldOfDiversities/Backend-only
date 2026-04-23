from rest_framework import serializers

from accounts.models import UserProfile
from sales.models import Sale

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    sale_id = serializers.PrimaryKeyRelatedField(
        queryset=Sale.objects.all(),
        source="sale",
        write_only=True,
    )
    processed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source="processed_by",
        write_only=True,
        allow_null=True,
        required=False,
    )
    sale_number = serializers.CharField(source="sale.sale_number", read_only=True)
    processed_by_name = serializers.CharField(source="processed_by.user.username", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "sale",
            "sale_id",
            "sale_number",
            "processed_by",
            "processed_by_id",
            "processed_by_name",
            "method",
            "amount",
            "reference",
            "status",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "sale",
            "processed_by",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return value

    def validate_reference(self, value: str) -> str:
        return value.strip()
