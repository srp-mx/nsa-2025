"""
WSGI config for the backend project.

This file configures the WSGI application for the project, which is used for
synchronous web servers and applications.
"""
import os
from django.core.wsgi import get_wsgi_application
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from flask_api import app as flask_app

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

django_app = get_wsgi_application()

application = DispatcherMiddleware(django_app, {
    '/api': flask_app,
})

