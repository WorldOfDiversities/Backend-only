from rest_framework import serializers

from accounts.models import UserProfile
from customers.models import Customer
from products.models import Product

from .models import Sale, SaleItem


class CheckoutItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class CheckoutRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    items = CheckoutItemInputSerializer(many=True)
    payment_method = serializers.ChoiceField(choices=['CASH', 'MOBILE_MONEY', 'CARD', 'SPLIT'])
    payment_reference = serializers.CharField(required=False, allow_blank=True, max_length=120)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def validate(self, attrs):
        payment_method = attrs.get("payment_method")
        payment_reference = (attrs.get("payment_reference") or "").strip()

        if payment_method in {"MOBILE_MONEY", "CARD", "SPLIT"} and not payment_reference:
            raise serializers.ValidationError(
                {"payment_reference": "Payment reference is required for electronic payments."}
            )

        return attrs


class CheckoutResponseSerializer(serializers.Serializer):
    sale_id = serializers.IntegerField()
    sale_number = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_id = serializers.IntegerField()
    receipt_id = serializers.IntegerField()


class SaleItemSerializer(serializers.ModelSerializer):
    sale_id = serializers.PrimaryKeyRelatedField(
        queryset=Sale.objects.all(),
        source="sale",
        write_only=True,
    )
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SaleItem
        fields = [
            "id",
            "sale",
            "sale_id",
            "product",
            "product_id",
            "product_name",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "sale",
            "product",
            "line_total",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def validate_quantity(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than zero.")
        return value


class SaleSerializer(serializers.ModelSerializer):
    cashier_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source="cashier",
        write_only=True,
        allow_null=True,
        required=False,
    )
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source="customer",
        write_only=True,
        allow_null=True,
        required=False,
    )
    cashier_name = serializers.CharField(source="cashier.user.username", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "sale_number",
            "cashier",
            "cashier_id",
            "cashier_name",
            "customer",
            "customer_id",
            "customer_name",
            "subtotal",
            "discount_amount",
            "tax_amount",
            "total_amount",
            "status",
            "notes",
            "item_count",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "sale_number",
            "cashier",
            "customer",
            "item_count",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def validate_subtotal(self, value):
        if value < 0:
            raise serializers.ValidationError("Subtotal cannot be negative.")
        return value

    def validate_discount_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Discount cannot be negative.")
        return value

    def validate_tax_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Tax cannot be negative.")
        return value

    def validate_total_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Total amount cannot be negative.")
        return value
