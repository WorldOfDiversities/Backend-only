from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    path('settings/', views.SystemSettingsView.as_view(), name='system-settings'),
    path('settings/upload-image/', views.SystemSettingsImageUploadView.as_view(), name='system-settings-upload-image'),
]
