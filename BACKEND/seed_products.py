#!/usr/bin/env python
"""
Seed script to populate products database with sample data.
Run with: python manage.py shell < seed_products.py
Or: python seed_products.py (requires Django setup in __main__)
"""

import os
import django

# Setup Django if running directly
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from products.models import Product, Category
from decimal import Decimal

def seed_products():
    """Seed database with 100+ sample products."""
    
    # Check existing products
    existing_count = Product.objects.count()
    print(f"Existing products in database: {existing_count}")
    
    if existing_count > 0:
        print(f"\n✓ Database has {existing_count} existing products. Adding new ones...\n")
    
    print("\nEnsuring all base categories exist...")
    
    # Create or get categories
    categories_data = {
        'Beverages': 'Drinks and beverages',
        'Food': 'Food items and snacks',
        'Household': 'Household goods and supplies',
        'Personal Care': 'Personal hygiene and care products',
        'Electronics': 'Electronic devices and accessories',
    }
    
    categories = {}
    for name, desc in categories_data.items():
        cat, created = Category.objects.get_or_create(
            name=name,
            defaults={'description': desc}
        )
        categories[name] = cat
        if created:
            print(f"  Created category: {name}")
        else:
            print(f"  Using existing category: {name}")
    
    # Sample products data
    products_data = [
        # Beverages
        ('Bottled Water 500ml', 'Beverages', Decimal('2.50'), 150),
        ('Bottled Water 1L', 'Beverages', Decimal('4.00'), 120),
        ('Fanta Orange 350ml', 'Beverages', Decimal('4.50'), 95),
        ('Fanta Grape 350ml', 'Beverages', Decimal('4.50'), 88),
        ('Coca-Cola 330ml', 'Beverages', Decimal('5.00'), 110),
        ('Sprite 330ml', 'Beverages', Decimal('5.00'), 105),
        ('Milo 400g', 'Beverages', Decimal('12.00'), 65),
        ('Nescafe Coffee 50g', 'Beverages', Decimal('8.50'), 45),
        ('Peak Milk Tin', 'Beverages', Decimal('18.00'), 40),
        ('Evaporated Milk 400ml', 'Beverages', Decimal('6.50'), 55),
        
        # Food
        ('Indomie Noodles Pack', 'Food', Decimal('5.00'), 200),
        ('Mama\'s Rice 1kg', 'Food', Decimal('15.00'), 60),
        ('Gari Flour 2kg', 'Food', Decimal('10.00'), 50),
        ('Cornflakes 500g', 'Food', Decimal('14.00'), 35),
        ('Bread Loaf Large', 'Food', Decimal('8.00'), 25),
        ('Cooking Oil 1L', 'Food', Decimal('22.00'), 40),
        ('Sugar 500g Pack', 'Food', Decimal('9.00'), 75),
        ('Salt 500g', 'Food', Decimal('3.50'), 100),
        ('Tomato Paste 400g', 'Food', Decimal('7.50'), 80),
        ('Fish 1kg', 'Food', Decimal('35.00'), 15),
        ('Chicken Pieces 1kg', 'Food', Decimal('32.00'), 20),
        ('Eggs Dozen', 'Food', Decimal('28.00'), 30),
        ('Butter 500g', 'Food', Decimal('18.00'), 22),
        ('Cheese 200g', 'Food', Decimal('15.00'), 18),
        ('Peanut Butter 400g', 'Food', Decimal('16.00'), 25),
        
        # Household
        ('Sunlight Soap Bar', 'Household', Decimal('6.00'), 120),
        ('Omo Detergent 500g', 'Household', Decimal('10.00'), 75),
        ('Dettol Soap 100g', 'Household', Decimal('8.00'), 95),
        ('Toilet Roll x4', 'Household', Decimal('12.00'), 50),
        ('Paper Towel Roll', 'Household', Decimal('5.50'), 65),
        ('Trash Bags 30L', 'Household', Decimal('8.50'), 80),
        ('Broom Stick', 'Household', Decimal('9.00'), 35),
        ('Mop Stick', 'Household', Decimal('11.00'), 28),
        ('Bucket 20L', 'Household', Decimal('18.00'), 20),
        ('Plate Set 6pc', 'Household', Decimal('32.00'), 12),
        ('Glass Set 6pc', 'Household', Decimal('28.00'), 15),
        ('Cutlery Set', 'Household', Decimal('26.00'), 10),
        ('Saucepan Large', 'Household', Decimal('48.00'), 8),
        ('Frying Pan', 'Household', Decimal('35.00'), 12),
        ('Cooking Pot 6L', 'Household', Decimal('52.00'), 7),
        
        # Personal Care
        ('Colgate Toothpaste 75ml', 'Personal Care', Decimal('9.00'), 110),
        ('Close-Up Toothpaste 75ml', 'Personal Care', Decimal('8.50'), 100),
        ('Sensodyne Toothpaste', 'Personal Care', Decimal('16.00'), 35),
        ('Toothbrush Standard', 'Personal Care', Decimal('5.00'), 150),
        ('Toothbrush Electric', 'Personal Care', Decimal('65.00'), 8),
        ('Shampoo 200ml', 'Personal Care', Decimal('12.00'), 85),
        ('Conditioner 200ml', 'Personal Care', Decimal('12.00'), 65),
        ('Body Soap Bar', 'Personal Care', Decimal('4.50'), 180),
        ('Vaseline 100ml', 'Personal Care', Decimal('7.00'), 90),
        ('Body Lotion 200ml', 'Personal Care', Decimal('14.00'), 55),
        ('Face Cream 50ml', 'Personal Care', Decimal('22.00'), 30),
        ('Deodorant Spray', 'Personal Care', Decimal('11.00'), 70),
        ('Perfume 100ml', 'Personal Care', Decimal('40.00'), 15),
        ('Razor Blade Pack 5', 'Personal Care', Decimal('8.50'), 95),
        ('Shaving Cream 200ml', 'Personal Care', Decimal('10.00'), 45),
        ('Hair Gel 200ml', 'Personal Care', Decimal('9.50'), 65),
        ('Hairbrush', 'Personal Care', Decimal('6.50'), 80),
        ('Hair Comb', 'Personal Care', Decimal('3.00'), 120),
        ('Baby Lotion 200ml', 'Personal Care', Decimal('16.00'), 25),
        ('Baby Powder 500g', 'Personal Care', Decimal('14.00'), 30),
        
        # Electronics
        ('USB Cable 1m', 'Electronics', Decimal('8.00'), 150),
        ('USB Cable 2m', 'Electronics', Decimal('10.00'), 120),
        ('Phone Charger Standard', 'Electronics', Decimal('18.00'), 60),
        ('Phone Charger Fast', 'Electronics', Decimal('35.00'), 30),
        ('Power Bank 5000mAh', 'Electronics', Decimal('45.00'), 20),
        ('Power Bank 10000mAh', 'Electronics', Decimal('75.00'), 15),
        ('HDMI Cable', 'Electronics', Decimal('25.00'), 25),
        ('Audio Cable 3.5mm', 'Electronics', Decimal('7.00'), 100),
        ('Headphones Basic', 'Electronics', Decimal('28.00'), 35),
        ('Headphones Premium', 'Electronics', Decimal('85.00'), 10),
        ('Speaker Portable', 'Electronics', Decimal('65.00'), 12),
        ('Lamp LED 9W', 'Electronics', Decimal('22.00'), 25),
        ('Bulb LED E27', 'Electronics', Decimal('12.00'), 60),
        ('Bulb LED E14', 'Electronics', Decimal('10.00'), 50),
        ('Extension Cord 5m', 'Electronics', Decimal('15.00'), 40),
        ('Power Strip 4 Outlet', 'Electronics', Decimal('32.00'), 20),
        ('Torch Flashlight', 'Electronics', Decimal('14.00'), 50),
        ('Batteries AA Pack 4', 'Electronics', Decimal('12.00'), 80),
        ('Batteries AAA Pack 4', 'Electronics', Decimal('10.00'), 70),
        ('SIM Card Holder', 'Electronics', Decimal('3.50'), 100),
    ]
    
    # Create products
    created_count = 0
    skipped_count = 0
    print(f"\nProcessing {len(products_data)} products...\n")
    
    for name, category_name, price, quantity in products_data:
        product, created = Product.objects.get_or_create(
            name=name,
            defaults={
                'category': categories[category_name],
                'price': price,
                'quantity': quantity,
                'is_active': True,
            }
        )
        if created:
            created_count += 1
            if created_count % 10 == 0:
                print(f"  Created {created_count} products...")
        else:
            skipped_count += 1
    
    print(f"\n✓ Seeding complete!")
    print(f"  Newly created products: {created_count}")
    print(f"  Skipped (already existed): {skipped_count}")
    print(f"  Total products in database: {Product.objects.count()}")
    
    # Print summary by category
    print("\nProducts by category:")
    for cat_name, category in categories.items():
        count = category.products.count()
        print(f"  - {cat_name}: {count} products")

if __name__ == "__main__":
    seed_products()
