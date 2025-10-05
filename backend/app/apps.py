"""
App configuration for the app.
"""
from django.apps import AppConfig


class MainConfig(AppConfig):
    """
    App configuration.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
