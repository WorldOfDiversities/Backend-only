from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('sales/daily/', views.DailySalesReportView.as_view(), name='sales-daily-report'),
    path('sales/weekly/', views.WeeklySalesReportView.as_view(), name='sales-weekly-report'),
    path('products/performance/', views.ProductPerformanceReportView.as_view(), name='product-performance-report'),
    path('inventory/summary/', views.InventorySummaryReportView.as_view(), name='inventory-summary-report'),
]
