from decimal import Decimal

from django.test import TestCase

from .serializers import ProductSerializer


class ProductSerializerTests(TestCase):
	def test_low_stock_threshold_must_be_at_least_one(self):
		serializer = ProductSerializer(
			data={
				"name": "Bottle Water",
				"price": Decimal("2.50"),
				"quantity": 1,
				"low_stock_threshold": 0,
			}
		)

		self.assertFalse(serializer.is_valid())
		self.assertIn("low_stock_threshold", serializer.errors)

	def test_low_stock_threshold_accepts_positive_value(self):
		serializer = ProductSerializer(
			data={
				"name": "Bottle Water",
				"price": Decimal("2.50"),
				"quantity": 1,
				"low_stock_threshold": 1,
			}
		)

		self.assertTrue(serializer.is_valid())
