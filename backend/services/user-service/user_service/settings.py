"""
Django settings for the User Service.

This is a microservice that handles:
- User registration and authentication
- Phone number verification (OTP)
- NRC encryption
- JWT token management
- User profiles and trust scores
"""
import os
from pathlib import Path
from decouple import config
from datetime import timedelta

# ============================================
# BASE DIRECTORY
# ============================================
# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# SECURITY SETTINGS
# ============================================
# SECRET_KEY: Used for cryptographic signing
# - Session cookies
# - Password reset tokens
# - CSRF tokens
# - JWT signing
SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-change-this-in-production')

# DEBUG: Development vs Production
# - True: Detailed error pages, auto-reload
# - False: Hide errors, better performance
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS: Which domains can access this service
# Separate with commas: localhost,127.0.0.1,api.agriconnect.com
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# ============================================
# INSTALLED APPS
# ============================================
# Django needs to know about all applications
# Order matters: Django apps first, then third-party, then our apps
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # PostGIS support for location data
    
    # Third-party apps
    'rest_framework',           # REST API framework
    'rest_framework_simplejwt', # JWT authentication
    'corsheaders',              # CORS support (frontend access)
    'django_filters',           # Filtering API results
    'phonenumber_field',        # Phone number validation
    'django_extensions',        # Development tools
    'django_celery_beat',       # Scheduled tasks
    'django_celery_results',    # Task tracking
    
    # Our apps
    'accounts',  # User management (custom user model)
]

# ============================================
# MIDDLEWARE
# ============================================
# Middleware runs on every request in order
# Each middleware can modify the request/response
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS must be early
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================
# URL CONFIGURATION
# ============================================
# Where Django looks for URL patterns
ROOT_URLCONF = 'user_service.urls'

# ============================================
# TEMPLATES
# ============================================
# For rendering HTML responses (admin, email templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================
# WSGI (Web Server Gateway Interface)
# ============================================
# For running with production servers (Gunicorn, uWSGI)
WSGI_APPLICATION = 'user_service.wsgi.application'

# ============================================
# DATABASE - PostgreSQL with PostGIS
# ============================================
# PostgreSQL with PostGIS for spatial queries
# Location data (GPS coordinates) stored as PostGIS points
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DB_NAME', default='agriconnect_user'),
        'USER': config('DB_USER', default='agriconnect_user'),
        'PASSWORD': config('DB_PASSWORD', default='agriconnect_pass'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,  # Keep connections alive for 60 seconds
    }
}

# ============================================
# AUTHENTICATION
# ============================================
# Custom user model (we'll define this in accounts/models.py)
# Instead of Django's default User model, we use our own
AUTH_USER_MODEL = 'accounts.User'

# Password validators ensure strong passwords
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================
# INTERNATIONALIZATION
# ============================================
# Set for Zambia
LANGUAGE_CODE = 'en-za'
TIME_ZONE = 'Africa/Lusaka'
USE_I18N = True
USE_TZ = True

# ============================================
# STATIC & MEDIA FILES
# ============================================
# Static files: CSS, JS, images for admin
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files: User uploads (NRC photos, profile pics)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================
# DEFAULT AUTO FIELD
# ============================================
# Use BigAutoField for primary keys (big integers)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# DJANGO REST FRAMEWORK
# ============================================
REST_FRAMEWORK = {
    # Authentication classes - how users authenticate
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Permission classes - who can access what
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Filtering - allow query parameters
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    # Pagination - how many results per page
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Throttling - rate limiting to prevent abuse
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',  # Anonymous users
        'rest_framework.throttling.UserRateThrottle',  # Authenticated users
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',    # Anonymous: 100 requests per hour
        'user': '1000/hour',   # Users: 1000 requests per hour
        'auth': '10/minute',   # Auth endpoints: 10 per minute
        'otp': '5/minute',     # OTP endpoints: 5 per minute
    },
}

# ============================================
# JWT SETTINGS
# ============================================
# JSON Web Tokens for authentication
# Tokens are stateless - no database lookup needed
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),   # Short-lived access
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # Long-lived refresh
    'ROTATE_REFRESH_TOKENS': True,                    # New refresh on use
    'BLACKLIST_AFTER_ROTATION': True,                 # Old tokens invalid
    'ALGORITHM': 'HS256',                             # Signing algorithm
    'SIGNING_KEY': SECRET_KEY,                        # Used for signing
    'AUTH_HEADER_TYPES': ('Bearer',),                 # Header: Bearer token
    'USER_ID_FIELD': 'id',                            # User identifier
    'USER_ID_CLAIM': 'user_id',                       # Claim name
}

# ============================================
# CORS SETTINGS
# ============================================
# Which frontend domains can access the API
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ============================================
# REDIS CACHE
# ============================================
# Used for:
# - Session storage
# - Rate limiting
# - OTP code storage
# - Caching frequent queries
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/1')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'user_service',  # Prefix all keys
        'TIMEOUT': 300,                # 5 minutes default
    }
}

# ============================================
# SESSION SETTINGS
# ============================================
# Store sessions in cache (Redis) for performance
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours

# ============================================
# CELERY - Background Tasks
# ============================================
# Celery handles background tasks:
# - Sending SMS OTP codes
# - Sending welcome emails
# - Running scheduled cleanups
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/2')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/3')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Lusaka'
CELERY_TASK_TRACK_STARTED = True

# ============================================
# LOGGING
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
}

# ============================================
# APPLICATION-SPECIFIC SETTINGS
# ============================================

# OTP Settings
OTP_EXPIRY_MINUTES = config('OTP_EXPIRY_MINUTES', default=5, cast=int)
MAX_VERIFICATION_ATTEMPTS = config('MAX_VERIFICATION_ATTEMPTS', default=5, cast=int)
MAX_PIN_ATTEMPTS = config('MAX_PIN_ATTEMPTS', default=3, cast=int)
ACCOUNT_LOCKOUT_MINUTES = config('ACCOUNT_LOCKOUT_MINUTES', default=30, cast=int)

# Trust Score Settings
TRUST_SCORE_STARTING = 50
TRUST_SCORE_MAX = 100
TRUST_SCORE_MIN = -100

# Africa's Talking - SMS Service
AFRICA_TALKING_USERNAME = config('AFRICA_TALKING_USERNAME', default='')
AFRICA_TALKING_API_KEY = config('AFRICA_TALKING_API_KEY', default='')
AFRICA_TALKING_SENDER_ID = config('AFRICA_TALKING_SENDER_ID', default='AgriConnect')
