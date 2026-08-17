"""
WSGI config for the User Service.

This is the entry point for WSGI servers like Gunicorn.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')
application = get_wsgi_application()
