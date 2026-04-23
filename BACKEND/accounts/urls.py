from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView,
    UserProfileViewSet,
    PasswordResetRequestView,
    PasswordResetTokenValidateView,
    PasswordResetConfirmView,
)

app_name = 'accounts'

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),

    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-validate/', PasswordResetTokenValidateView.as_view(), name='password-reset-validate'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
