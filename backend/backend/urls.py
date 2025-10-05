"""
URL configuration for the backend project.

This file defines the URL patterns for the entire project. It maps URLs to
views, allowing the Django framework to route requests to the appropriate
view function.
"""
from django.contrib import admin
from django.urls import path
from app import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

urlpatterns = [
    # Signup
    path("auth/signup/", views.signup_view, name="signup"),
    path("auth/login/", views.login_view, name="login"),
    # Refresh access token
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Logout (blacklist refresh token)
    path("auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path('admin/', admin.site.urls),
    # Organizations
    path("organizations/", views.organization_list),
    path("organizations/<int:pk>/", views.organization_detail),
    # Sites
    path("sites/", views.site_list),
    path("sites/<int:pk>/", views.site_detail),
    # Auditors
    path("auditors/", views.auditor_list),
    path("auditors/<int:pk>/", views.auditor_detail),
    # Audits
    path("audits/", views.audit_list),
    path("audits/<int:pk>/", views.audit_detail),
    # Measurements
    path("measurements/", views.measurement_list),
    path("measurements/<int:pk>/", views.measurement_detail),
    # NASA Earthdata API
    path("health/", views.health_check, name="health_check"),
    path("api/map/current/", views.get_current_map, name="get_current_map"),
    path("api/data/range/", views.get_data_range, name="get_data_range"),
]
