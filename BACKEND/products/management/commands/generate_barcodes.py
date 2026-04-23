import uuid
from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
	help = 'Generate barcodes for products that do not have one'

	def add_arguments(self, parser):
		parser.add_argument(
			'--prefix',
			type=str,
			default='POS',
			help='Prefix for generated barcode codes'
		)

	def handle(self, *args, **options):
		prefix = options['prefix']
		products_without_barcode = Product.objects.filter(barcode__isnull=True, is_deleted=False)
		
		count = 0
		for product in products_without_barcode:
			# Generate barcode: PREFIX-SKUPART-RANDOMPORTION
			# Example: POS-SKU1234567-AB12CD
			random_part = uuid.uuid4().hex[:6].upper()
			product.barcode = f"{prefix}-{product.sku.split('-')[1] if '-' in product.sku else 'GEN'}-{random_part}"
			product.save()
			count += 1
			self.stdout.write(
				self.style.SUCCESS(f'✓ {product.name}: {product.barcode}')
			)

		self.stdout.write(
			self.style.SUCCESS(f'\nSuccessfully generated barcodes for {count} products.')
		)
