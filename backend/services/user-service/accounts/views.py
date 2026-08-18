"""
Default views for the accounts app.

Note: API views are in accounts/api/views.py
This file is kept for Django's app structure but is not used for the API.
"""
from django.shortcuts import render
from django.http import HttpResponse

# Import from local enums (NOT shared)
from .enums import UserRole


def index(request):
    """Simple index view (not used in API)."""
    return HttpResponse("Accounts app is running. Use /api/v1/ for API endpoints.")
