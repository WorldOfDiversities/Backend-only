from django.urls import path
from . import views

app_name = 'backups'

urlpatterns = [
    # Backup endpoints
    # path('backup/', views.BackupView.as_view(), name='backup'),
    # path('restore/', views.RestoreView.as_view(), name='restore'),
]
