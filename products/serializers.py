from rest_framework import serializers

from .models import Category, Product, Supplier


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "deleted_at"]

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Category name is required.")
        return cleaned


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "phone_number",
            "email",
            "address",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "deleted_at"]

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Supplier name is required.")
        return cleaned


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        allow_null=True,
        required=False,
    )
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source="supplier",
        write_only=True,
        allow_null=True,
        required=False,
    )
    category_name = serializers.CharField(source="category.name", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "category",
            "category_id",
            "category_name",
            "supplier",
            "supplier_id",
            "supplier_name",
            "barcode",
            "price",
            "quantity",
            "low_stock_threshold",
            "is_low_stock",
            "is_active",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "sku",
            "category",
            "supplier",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Product name is required.")
        return cleaned

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_low_stock_threshold(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Low stock threshold must be at least 1.")
        return value
