from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse

# ============================================================================
# FRONTEND VIEWS
# ============================================================================

def landing(request):
    """Landing page view."""
    return render(request, 'landing.html')

def register(request):
    """Registration page view."""
    if request.method == 'POST':
        # TODO: Implement registration
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    return render(request, 'register.html')

@login_required
def dashboard(request):
    """Dashboard view."""
    return render(request, 'dashboard.html', {'user': request.user})

@login_required
def listings(request):
    """Listings page view."""
    return render(request, 'listings.html', {'user': request.user})

# ============================================================================
# API VIEWS (Keep existing API views here)
# ============================================================================
# ... your existing API views ...
