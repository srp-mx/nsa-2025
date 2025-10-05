"""
URL configuration for the backend project.

This file defines the URL patterns for the entire project. It maps URLs to
views, allowing the Django framework to route requests to the appropriate
view function.
"""
from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    # Organizations
    path("organizations/", views.organization_list),
    path("organizations/<int:pk>/", views.organization_detail),
    # Auditors
    path("auditors/", views.auditor_list),
    path("auditors/<int:pk>/", views.auditor_detail),
    # Audits
    path("audits/", views.audit_list),
    path("audits/<int:pk>/", views.audit_detail),
    # Measurements
    path("measurements/", views.measurement_list),
    path("measurements/<int:pk>/", views.measurement_detail),
    # TODO: visualizar measurements
    # TODO: login/logout
]
