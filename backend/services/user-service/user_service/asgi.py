"""
ASGI config for the User Service.

This is the entry point for ASGI servers like Daphne.
Used for WebSocket support (if needed in the future).
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')
application = get_asgi_application()
