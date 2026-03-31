from django.core.validators import MinValueValidator
from django.db import migrations, models


def set_zero_thresholds_to_default(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.filter(low_stock_threshold=0).update(low_stock_threshold=5)


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(set_zero_thresholds_to_default, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="low_stock_threshold",
            field=models.PositiveIntegerField(default=5, validators=[MinValueValidator(1)]),
        ),
    ]
