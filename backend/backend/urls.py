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
]
