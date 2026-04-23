from datetime import timedelta

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrManager
from payments.models import Payment
from products.models import Product
from sales.models import Sale, SaleItem


class BaseReportView(APIView):
	permission_classes = [IsAuthenticated, IsAdminOrManager]

	@staticmethod
	def _resolve_date_range(request, default_days: int = 7):
		today = timezone.localdate()
		end_date = parse_date(request.query_params.get("end_date", "")) or today
		start_date = parse_date(request.query_params.get("start_date", "")) or (end_date - timedelta(days=default_days - 1))
		if start_date > end_date:
			start_date, end_date = end_date, start_date
		return start_date, end_date

	@staticmethod
	def _safe_int(value, default: int, min_value: int, max_value: int) -> int:
		try:
			parsed = int(value)
		except (TypeError, ValueError):
			parsed = default
		return max(min_value, min(parsed, max_value))


class DailySalesReportView(BaseReportView):
	def get(self, request):
		start_date, end_date = self._resolve_date_range(request, default_days=7)
		sales_qs = (
			Sale.objects.filter(
				status=Sale.Status.COMPLETED,
				created_at__date__gte=start_date,
				created_at__date__lte=end_date,
			)
			.annotate(report_date=TruncDate("created_at"))
			.values("report_date")
			.annotate(
				sales_count=Count("id"),
				gross_total=Sum("total_amount"),
			)
			.order_by("report_date")
		)

		payment_breakdown = (
			Payment.objects.filter(
				status=Payment.Status.COMPLETED,
				created_at__date__gte=start_date,
				created_at__date__lte=end_date,
			)
			.values("method")
			.annotate(total=Sum("amount"), payments=Count("id"))
			.order_by("method")
		)

		return Response(
			{
				"start_date": start_date,
				"end_date": end_date,
				"daily": list(sales_qs),
				"payment_breakdown": list(payment_breakdown),
			}
		)


class WeeklySalesReportView(BaseReportView):
	def get(self, request):
		weeks = self._safe_int(request.query_params.get("weeks", 8), default=8, min_value=1, max_value=52)
		end_date = timezone.localdate()
		start_date = end_date - timedelta(days=(weeks * 7) - 1)

		weekly_sales = (
			Sale.objects.filter(
				status=Sale.Status.COMPLETED,
				created_at__date__gte=start_date,
				created_at__date__lte=end_date,
			)
			.annotate(week_start=TruncWeek("created_at"))
			.values("week_start")
			.annotate(sales_count=Count("id"), gross_total=Sum("total_amount"))
			.order_by("week_start")
		)

		return Response(
			{
				"weeks": weeks,
				"start_date": start_date,
				"end_date": end_date,
				"weekly": list(weekly_sales),
			}
		)


class ProductPerformanceReportView(BaseReportView):
	def get(self, request):
		start_date, end_date = self._resolve_date_range(request, default_days=30)
		limit = self._safe_int(request.query_params.get("limit", 10), default=10, min_value=1, max_value=100)

		product_rows = (
			SaleItem.objects.filter(
				sale__status=Sale.Status.COMPLETED,
				sale__created_at__date__gte=start_date,
				sale__created_at__date__lte=end_date,
			)
			.values("product__id", "product__name", "product__sku", "product__category__name")
			.annotate(
				units_sold=Sum("quantity"),
				revenue=Sum("line_total"),
				sale_lines=Count("id"),
			)
			.order_by("-revenue", "-units_sold")[:limit]
		)

		return Response(
			{
				"start_date": start_date,
				"end_date": end_date,
				"limit": limit,
				"top_products": list(product_rows),
			}
		)


class InventorySummaryReportView(BaseReportView):
	def get(self, request):
		products_qs = Product.objects.filter(is_deleted=False)

		inventory_totals = products_qs.aggregate(
			total_products=Count("id"),
			active_products=Count("id", filter=Q(is_active=True)),
			total_units=Sum("quantity"),
		)

		low_stock_qs = (
			products_qs.filter(is_active=True, quantity__lte=F("low_stock_threshold"))
			.values("id", "name", "sku", "quantity", "low_stock_threshold")
			.order_by("quantity", "name")
		)

		return Response(
			{
				"summary": inventory_totals,
				"low_stock": list(low_stock_qs),
			}
		)
