"""
API v1 URL Configuration

Centralized routing for all versioned API endpoints.
Each app has its own urls.py (separated concerns).
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import RoleAwareTokenObtainPairView

app_name = 'api_v1'

urlpatterns = [
    path('auth/token/', RoleAwareTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Authentication & Accounts
    path('auth/', include('accounts.urls')),
    
    # Products & Categories
    path('products/', include('products.urls')),
    
    # Inventory Management
    path('inventory/', include('inventory.urls')),
    
    # Customers & Loyalty
    path('customers/', include('customers.urls')),
    
    # Sales Transactions
    path('sales/', include('sales.urls')),
    
    # Payments
    path('payments/', include('payments.urls')),
    
    # Receipts
    path('receipts/', include('receipts.urls')),
    
    # Reporting & Analytics
    path('reports/', include('reports.urls')),
    
    # Audit Logs
    path('auditlog/', include('auditlog.urls')),
    
    # Backup & Restore
    path('backups/', include('backups.urls')),
    
    # Common/Shared
    path('common/', include('common.urls')),
]
