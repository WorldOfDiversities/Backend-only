from rest_framework import serializers

from payments.models import Payment
from sales.models import Sale

from .models import Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    sale_id = serializers.PrimaryKeyRelatedField(
        queryset=Sale.objects.all(),
        source="sale",
        write_only=True,
    )
    payment_id = serializers.PrimaryKeyRelatedField(
        queryset=Payment.objects.all(),
        source="payment",
        write_only=True,
        allow_null=True,
        required=False,
    )
    sale_number = serializers.CharField(source="sale.sale_number", read_only=True)

    class Meta:
        model = Receipt
        fields = [
            "id",
            "sale",
            "sale_id",
            "sale_number",
            "payment",
            "payment_id",
            "receipt_number",
            "store_name",
            "payload",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "sale",
            "payment",
            "receipt_number",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def validate_store_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Store name is required.")
        return cleaned

    def validate_payload(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Payload must be a JSON object.")
        return value
