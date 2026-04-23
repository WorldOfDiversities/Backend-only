from __future__ import annotations

import os
from decimal import Decimal
from itertools import cycle

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import UserProfile
from auditlog.models import AuditLog
from common.models import SystemSettings
from customers.models import Customer
from inventory.models import InventoryAlert, StockMovement
from payments.models import Payment
from products.models import Category, Product, Supplier
from receipts.models import Receipt
from sales.models import Sale, SaleItem
from seed_products import seed_products as seed_products_script


DEMO_PASSWORD = "Admin@12345"
MONEY = Decimal("0.01")


def q(value: Decimal | str | int | float) -> Decimal:
	return Decimal(str(value)).quantize(MONEY)


def control(section: str, index: int, kind: str, value):
	state = {"key": f"{section}:{index}", "type": kind}
	if kind == "checkbox":
		state["checked"] = bool(value)
	else:
		state["value"] = value
	return state


def controls(section: str, items: list[tuple[str, object]]) -> list[dict[str, object]]:
	return [control(section, index, kind, value) for index, (kind, value) in enumerate(items)]


class Command(BaseCommand):
	help = "Seed a complete demo dataset for the POS database."

	def add_arguments(self, parser):
		parser.add_argument(
			"--password",
			type=str,
			default=None,
			help="Password to set on the demo accounts. Defaults to Admin@12345 or SEED_DEMO_PASSWORD.",
		)

	def handle(self, *args, **options):
		demo_password = (
			options.get("password")
			or os.environ.get("SEED_DEMO_PASSWORD")
			or DEMO_PASSWORD
		)

		with transaction.atomic():
			self.stdout.write(self.style.MIGRATE_HEADING("Seeding demo users and profiles..."))
			admin_user, admin_profile = self.ensure_user(
				username="admin",
				password=demo_password,
				first_name="Admin",
				last_name="User",
				email="admin@swiftpos.com",
				role=UserProfile.Role.ADMIN,
				phone_number="+233 24 000 0001",
				is_staff=True,
				is_superuser=True,
			)
			manager_user, manager_profile = self.ensure_user(
				username="manager",
				password=demo_password,
				first_name="Akosua",
				last_name="Mensah",
				email="manager@swiftpos.com",
				role=UserProfile.Role.MANAGER,
				phone_number="+233 24 000 0002",
			)
			cashier_one_user, cashier_one_profile = self.ensure_user(
				username="cashier1",
				password=demo_password,
				first_name="Ama",
				last_name="Darko",
				email="ama@swiftpos.com",
				role=UserProfile.Role.CASHIER,
				phone_number="+233 24 000 0003",
			)
			cashier_two_user, cashier_two_profile = self.ensure_user(
				username="cashier2",
				password=demo_password,
				first_name="Kofi",
				last_name="Boateng",
				email="kofi@swiftpos.com",
				role=UserProfile.Role.CASHIER,
				phone_number="+233 24 000 0004",
			)
			self.stdout.write(self.style.SUCCESS("✓ Users and profiles ready"))

			self.stdout.write(self.style.MIGRATE_HEADING("Seeding system settings..."))
			SystemSettings.objects.update_or_create(
				key="default",
				defaults={
					"store_profile": {
						"controls": controls(
							"sec-store",
							[
								("text", "SwiftPOS Store"),
								("text", "KSI-001"),
								("text", "Adum, Kumasi, Ashanti Region, Ghana"),
								("text", "+233 32 202 0000"),
								("text", "store@swiftpos.com"),
								("text", "GH-BUS-20240011"),
								("text", "Your trusted neighbourhood retail store — fast, fresh, and friendly."),
								("text", "07:00"),
								("text", "20:00"),
								("text", "GMT+0 (Accra)"),
								("checkbox", True),
								("checkbox", True),
							],
						),
						"logo_data_url": "",
					},
					"appearance": {
						"theme_color": "#0f1f3d",
						"theme_label": "Navy (Default)",
						"profile_photo_data_url": "",
					},
					"regional": {
						"controls": controls(
							"sec-regional",
							[
								("text", "GHS — Ghanaian Cedi (GH₵)"),
								("text", "English (Ghana)"),
								("text", "DD/MM/YYYY"),
								("text", "12-hour (AM/PM)"),
								("text", "Period ( . )"),
								("text", "Comma ( , )"),
							],
						),
					},
					"pos": {
						"controls": controls(
							"sec-pos",
							[
								("checkbox", True),
								("checkbox", False),
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("text", "50"),
								("text", "30 min"),
							],
						),
					},
					"receipt": {
						"controls": controls(
							"sec-receipt",
							[
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("checkbox", False),
								("text", "Thank you for shopping with us! Visit again soon."),
							],
						),
					},
					"payment": {
						"controls": controls(
							"sec-payment",
							[
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("checkbox", False),
								("checkbox", True),
								("text", "024 XXX XXXX"),
								("text", "020 XXX XXXX"),
								("text", "027 XXX XXXX"),
								("text", "SwiftPOS Store"),
							],
						),
					},
					"tax": {
						"controls": controls(
							"sec-tax",
							[
								("checkbox", True),
								("checkbox", False),
								("text", "VAT"),
								("text", "5"),
								("checkbox", True),
								("text", "10"),
								("checkbox", True),
							],
						),
					},
					"notifications": {
						"controls": controls(
							"sec-notifications",
							[
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("checkbox", False),
								("checkbox", False),
								("checkbox", True),
								("checkbox", True),
								("checkbox", False),
							],
						),
						"values": {
							"low_stock_alerts": True,
							"daily_sales_summary": True,
							"large_transaction_alert": True,
							"failed_login_attempts": True,
							"refund_processed": False,
							"new_customer_registration": False,
							"in_app_notifications": True,
							"email_notifications": True,
							"sms_alerts": False,
						},
					},
					"security": {
						"controls": controls(
							"sec-security",
							[
								("checkbox", True),
								("checkbox", True),
								("checkbox", True),
								("text", "30"),
							],
						),
						"values": {
							"two_factor_auth": True,
							"force_password_change_90_days": True,
							"lock_after_failed_logins": True,
							"session_timeout_minutes": "30",
						},
					},
					"backup": {
						"controls": controls(
							"sec-backup",
							[
								("checkbox", True),
								("text", "Daily"),
								("text", "30 days"),
							],
						),
						"values": {
							"enable_auto_backup": True,
							"backup_frequency": "Daily",
							"backup_retention_days": "30 days",
						},
					},
					"staff": [
						{"username": admin_user.username, "name": "Admin User", "role": "ADMIN", "phone_number": admin_profile.phone_number},
						{"username": manager_user.username, "name": "Akosua Mensah", "role": "MANAGER", "phone_number": manager_profile.phone_number},
						{"username": cashier_one_user.username, "name": "Ama Darko", "role": "CASHIER", "phone_number": cashier_one_profile.phone_number},
						{"username": cashier_two_user.username, "name": "Kofi Boateng", "role": "CASHIER", "phone_number": cashier_two_profile.phone_number},
					],
				},
			)
			self.stdout.write(self.style.SUCCESS("✓ System settings ready"))

			self.stdout.write(self.style.MIGRATE_HEADING("Seeding categories, suppliers, and products..."))
			categories = self.seed_categories()
			suppliers = self.seed_suppliers()
			seed_products_script()
			self.assign_suppliers_to_products(suppliers)
			self.tune_product_demo_state()
			self.stdout.write(self.style.SUCCESS("✓ Product catalog ready"))

			self.stdout.write(self.style.MIGRATE_HEADING("Seeding customers, inventory, sales, payments, receipts, and audit logs..."))
			customers = self.seed_customers()
			product_map = {product.name: product for product in Product.objects.all()}
			self.seed_inventory(product_map, admin_profile, manager_profile)
			self.seed_sales(product_map, customers, cashier_one_profile, cashier_two_profile, admin_user)
			self.seed_audit_logs(admin_user, manager_user, cashier_one_user, cashier_two_user)

			self.stdout.write(self.style.SUCCESS("\n✓ Comprehensive demo seed completed successfully."))

	def ensure_user(
		self,
		*,
		username: str,
		password: str,
		first_name: str,
		last_name: str,
		email: str,
		role: str,
		phone_number: str,
		is_staff: bool = False,
		is_superuser: bool = False,
	):
		user, _ = User.objects.get_or_create(username=username)
		user.first_name = first_name
		user.last_name = last_name
		user.email = email
		user.is_staff = is_staff
		user.is_superuser = is_superuser
		user.is_active = True
		user.set_password(password)
		user.save()

		profile, _ = UserProfile.objects.get_or_create(user=user)
		profile.role = role
		profile.phone_number = phone_number
		profile.save()
		return user, profile

	def seed_categories(self):
		items = [
			("Beverages", "Drinks and beverages"),
			("Food", "Food items and snacks"),
			("Household", "Household goods and supplies"),
			("Personal Care", "Personal hygiene and care products"),
			("Electronics", "Electronic devices and accessories"),
			("Stationery", "Office and school stationery"),
			("Health", "Basic over-the-counter health items"),
		]
		return {
			name: Category.objects.update_or_create(name=name, defaults={"description": description})[0]
			for name, description in items
		}

	def seed_suppliers(self):
		items = [
			("Swift Wholesale Ltd", "+233 54 100 0001", "orders@swiftwholesale.com", "Industrial Area, Kumasi"),
			("Gold Coast Foods", "+233 54 100 0002", "sales@goldcoastfoods.com", "Tema Port Road, Accra"),
			("FreshCare Distribution", "+233 54 100 0003", "hello@freshcare.com", "Spintex Road, Accra"),
			("TechLine Supplies", "+233 54 100 0004", "support@techline.com", "Airport Residential, Accra"),
			("HouseHold Mart", "+233 54 100 0005", "orders@householdmart.com", "Adum, Kumasi"),
		]
		return [
			Supplier.objects.update_or_create(
				name=name,
				defaults={"phone_number": phone, "email": email, "address": address},
			)[0]
			for name, phone, email, address in items
		]

	def assign_suppliers_to_products(self, suppliers: list[Supplier]):
		products = list(Product.objects.filter(is_deleted=False).order_by("name"))
		if not products or not suppliers:
			return

		for product, supplier in zip(products, cycle(suppliers)):
			if product.supplier_id != supplier.id:
				product.supplier = supplier
				product.save(update_fields=["supplier", "updated_at"])

	def tune_product_demo_state(self):
		low_stock_targets = {
			"Dettol Soap 100g": (3, 5),
			"SIM Card Holder": (2, 5),
			"Torch Flashlight": (4, 5),
			"Batteries AA Pack 4": (4, 5),
		}
		for name, (quantity, threshold) in low_stock_targets.items():
			product = Product.objects.filter(name=name).first()
			if not product:
				continue
			product.quantity = quantity
			product.low_stock_threshold = threshold
			product.save(update_fields=["quantity", "low_stock_threshold", "updated_at"])

	def seed_customers(self):
		items = [
			("CUS-0001", "Kwame Mensah", "+233 24 300 1001", "kwame@example.com", "Adum, Kumasi", 480),
			("CUS-0002", "Akua Boateng", "+233 24 300 1002", "akua@example.com", "Asokwa, Kumasi", 150),
			("CUS-0003", "Yaw Asante", "+233 24 300 1003", "yaw@example.com", "Tech Junction, Kumasi", 90),
			("CUS-0004", "Esi Ofori", "+233 24 300 1004", "esi@example.com", "Santasi, Kumasi", 230),
			("CUS-0005", "Nana Amoah", "+233 24 300 1005", "nana@example.com", "Airport, Kumasi", 60),
			("CUS-0006", "Abena Serwaa", "+233 24 300 1006", "abena@example.com", "Tafo, Kumasi", 300),
		]
		customers = []
		for customer_code, name, phone_number, email, address, points in items:
			customer, _ = Customer.objects.update_or_create(
				customer_code=customer_code,
				defaults={
					"name": name,
					"phone_number": phone_number,
					"email": email,
					"address": address,
					"loyalty_points": points,
					"is_active": True,
				},
			)
			customers.append(customer)
		self.stdout.write(self.style.SUCCESS(f"✓ Customers ready ({len(customers)})"))
		return customers

	def seed_inventory(self, product_map, admin_profile, manager_profile):
		restock_events = [
			("Bottled Water 500ml", 120, "Initial stock allocation"),
			("Indomie Noodles Pack", 180, "Warehouse restock"),
			("Sunlight Soap Bar", 90, "Shelf refill"),
			("USB Cable 1m", 60, "Electronics restock"),
		]
		for product_name, quantity, note in restock_events:
			product = product_map.get(product_name)
			if not product:
				continue
			StockMovement.objects.get_or_create(
				product=product,
				movement_type=StockMovement.MovementType.RESTOCK,
				quantity=quantity,
				note=note,
				performed_by=manager_profile,
			)

		adjustment_events = [
			("Dettol Soap 100g", -2, "Seed adjustment to create low stock example"),
			("Batteries AA Pack 4", -3, "Sample shrinkage adjustment"),
		]
		for product_name, quantity, note in adjustment_events:
			product = product_map.get(product_name)
			if not product:
				continue
			StockMovement.objects.get_or_create(
				product=product,
				movement_type=StockMovement.MovementType.ADJUSTMENT,
				quantity=quantity,
				note=note,
				performed_by=admin_profile,
			)

		alert_targets = [
			("Dettol Soap 100g", "Dettol Soap 100g is below the minimum stock threshold."),
			("SIM Card Holder", "SIM Card Holder stock is critically low."),
			("Torch Flashlight", "Torch Flashlight stock is running low."),
		]
		for product_name, message in alert_targets:
			product = product_map.get(product_name)
			if not product:
				continue
			InventoryAlert.objects.get_or_create(
				product=product,
				message=message,
				defaults={"is_resolved": False},
			)

		self.stdout.write(self.style.SUCCESS("✓ Inventory activity ready"))

	def seed_sales(self, product_map, customers, cashier_one_profile, cashier_two_profile, admin_user):
		orders = [
			{
				"sale_number": "SAL-DEMO-0001",
				"cashier": cashier_one_profile,
				"customer": customers[0],
				"items": [
					("Bottled Water 500ml", 6, "2.50"),
					("Indomie Noodles Pack", 4, "5.00"),
					("Sunlight Soap Bar", 2, "6.00"),
				],
				"discount": "0.00",
				"tax_rate": Decimal("0.05"),
				"payment_method": Payment.Method.CASH,
				"payment_reference": "CASH-SEED-0001",
				"receipt_number": "RCP-SEED-0001",
				"notes": "Morning opening sale",
			},
			{
				"sale_number": "SAL-DEMO-0002",
				"cashier": cashier_two_profile,
				"customer": customers[1],
				"items": [
					("Omo Detergent 500g", 2, "10.00"),
					("Dettol Soap 100g", 5, "8.00"),
					("Toothbrush Standard", 4, "5.00"),
				],
				"discount": "3.00",
				"tax_rate": Decimal("0.05"),
				"payment_method": Payment.Method.MOBILE_MONEY,
				"payment_reference": "MOMO-SEED-0002",
				"receipt_number": "RCP-SEED-0002",
				"notes": "Household and personal care",
			},
			{
				"sale_number": "SAL-DEMO-0003",
				"cashier": cashier_one_profile,
				"customer": customers[2],
				"items": [
					("USB Cable 1m", 3, "8.00"),
					("Phone Charger Fast", 1, "35.00"),
					("Power Bank 10000mAh", 1, "75.00"),
				],
				"discount": "10.00",
				"tax_rate": Decimal("0.05"),
				"payment_method": Payment.Method.CARD,
				"payment_reference": "CARD-SEED-0003",
				"receipt_number": "RCP-SEED-0003",
				"notes": "Electronics sale",
			},
			{
				"sale_number": "SAL-DEMO-0004",
				"cashier": cashier_two_profile,
				"customer": customers[3],
				"items": [
					("Milo 400g", 2, "12.00"),
					("Fanta Orange 350ml", 6, "4.50"),
					("Eggs Dozen", 1, "28.00"),
				],
				"discount": "0.00",
				"tax_rate": Decimal("0.05"),
				"payment_method": Payment.Method.SPLIT,
				"payment_reference": "SPLIT-SEED-0004",
				"receipt_number": "RCP-SEED-0004",
				"notes": "Mixed basket order",
			},
		]

		for order in orders:
			sale, created = Sale.objects.get_or_create(
				sale_number=order["sale_number"],
				defaults={
					"cashier": order["cashier"],
					"customer": order["customer"],
					"subtotal": Decimal("0.00"),
					"discount_amount": q(order["discount"]),
					"tax_amount": Decimal("0.00"),
					"total_amount": Decimal("0.00"),
					"status": Sale.Status.COMPLETED,
					"notes": order["notes"],
				},
			)

			subtotal = Decimal("0.00")
			created_items = 0
			for product_name, quantity, unit_price in order["items"]:
				product = product_map.get(product_name)
				if not product:
					continue
				unit_price_decimal = q(unit_price)
				line_total = q(Decimal(quantity) * unit_price_decimal)
				sale_item, sale_item_created = SaleItem.objects.get_or_create(
					sale=sale,
					product=product,
					defaults={
						"quantity": quantity,
						"unit_price": unit_price_decimal,
						"line_total": line_total,
					},
				)
				if sale_item_created:
					created_items += 1
					product.quantity = max(product.quantity - quantity, 0)
					product.save(update_fields=["quantity", "updated_at"])
					StockMovement.objects.get_or_create(
						product=product,
						movement_type=StockMovement.MovementType.SALE,
						quantity=-quantity,
						note=f"Seed sale {order['sale_number']}",
						performed_by=order["cashier"],
					)
				subtotal += q(Decimal(quantity) * unit_price_decimal)

			discount = q(order["discount"])
			tax = q((subtotal - discount) * order["tax_rate"])
			total = q(subtotal - discount + tax)
			sale.cashier = order["cashier"]
			sale.customer = order["customer"]
			sale.subtotal = subtotal
			sale.discount_amount = discount
			sale.tax_amount = tax
			sale.total_amount = total
			sale.status = Sale.Status.COMPLETED
			sale.notes = order["notes"]
			sale.save()

			payment, payment_created = Payment.objects.get_or_create(
				reference=order["payment_reference"],
				defaults={
					"sale": sale,
					"processed_by": order["cashier"],
					"method": order["payment_method"],
					"amount": total,
					"status": Payment.Status.COMPLETED,
				},
			)
			if not payment_created and payment.sale_id != sale.id:
				payment.sale = sale
				payment.processed_by = order["cashier"]
				payment.method = order["payment_method"]
				payment.amount = total
				payment.status = Payment.Status.COMPLETED
				payment.save()

			Receipt.objects.get_or_create(
				receipt_number=order["receipt_number"],
				defaults={
					"sale": sale,
					"payment": payment,
					"store_name": "SwiftPOS Store",
					"payload": {
						"sale_number": sale.sale_number,
						"cashier": f"{order['cashier'].user.first_name} {order['cashier'].user.last_name}".strip(),
						"customer": order["customer"].name,
						"subtotal": str(subtotal),
						"discount": str(discount),
						"tax": str(tax),
						"total": str(total),
						"items": [
							{
								"product": item[0],
								"quantity": item[1],
								"unit_price": item[2],
							}
							for item in order["items"]
						],
					},
				},
			)

			self.stdout.write(
				self.style.SUCCESS(
					f"  ✓ {sale.sale_number}: {'created' if created else 'updated'} | items {created_items} | total GH₵ {total}"
				)
			)

		self.stdout.write(self.style.SUCCESS("✓ Sales, payments, and receipts ready"))

	def seed_audit_logs(self, admin_user, manager_user, cashier_one_user, cashier_two_user):
		entries = [
			(admin_user, AuditLog.Action.LOGIN, "User", "admin", "Admin logged in to manage the store"),
			(manager_user, AuditLog.Action.STOCK_ADJUSTMENT, "Inventory", "DET-TOL-100", "Adjusted Dettol Soap low stock after stocktake"),
			(cashier_one_user, AuditLog.Action.SALE, "Sale", "SAL-DEMO-0001", "Processed morning opening sale"),
			(cashier_two_user, AuditLog.Action.PAYMENT, "Payment", "MOMO-SEED-0002", "Captured mobile money payment for household basket"),
			(admin_user, AuditLog.Action.UPDATE, "SystemSettings", "default", "Configured system settings for the demo environment"),
			(cashier_one_user, AuditLog.Action.LOGOUT, "User", "cashier1", "Cashier logged out after shift"),
			(cashier_two_user, AuditLog.Action.CREATE, "Customer", "CUS-0006", "Added a new loyalty customer"),
		]

		for actor, action, entity_type, entity_id, description in entries:
			AuditLog.objects.get_or_create(
				action=action,
				entity_type=entity_type,
				entity_id=entity_id,
				defaults={
					"actor": actor,
					"description": description,
					"metadata": {},
				},
			)

		self.stdout.write(self.style.SUCCESS("✓ Audit logs ready"))
