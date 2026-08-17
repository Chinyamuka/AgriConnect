"""
Custom User model for AgriConnect.

This extends Django's AbstractUser to add:
- Phone as the primary identifier
- NRC encryption
- Role-based access (Farmer, Buyer, Transporter, Admin)
- Trust scores
- Location data (PostGIS)
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db.models import PointField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from fernet_fields import EncryptedCharField
from django.conf import settings
from shared.models import BaseModel
from shared.models.enums import UserRole, Language


class User(BaseModel, AbstractUser):
    """
    Custom User model with phone as primary identifier.
    
    Inherits from:
    - BaseModel: Provides UUID, created_at, updated_at
    - AbstractUser: Provides username, password, email, etc.
    """
    # Remove username field (we use phone instead)
    username = None
    
    # Override fields from AbstractUser
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    
    # Core fields
    phone = PhoneNumberField(
        unique=True,
        help_text="Phone number in E.164 format"
    )
    nrc = EncryptedCharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="National Registration Card number (encrypted at rest)"
    )
    
    # Role (Farmer, Buyer, Transporter, Admin)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.FARMER,
        help_text="User's role in the system"
    )
    
    # Verification and security
    is_verified = models.BooleanField(
        default=False,
        help_text="Phone and NRC verified"
    )
    is_blacklisted = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Trust score (-100 to 100)
    trust_score = models.IntegerField(
        default=settings.TRUST_SCORE_STARTING,
        validators=[
            MinValueValidator(settings.TRUST_SCORE_MIN),
            MaxValueValidator(settings.TRUST_SCORE_MAX)
        ],
        help_text="User trust score (-100 to 100)"
    )
    
    # Location (PostGIS Point)
    location = PointField(
        srid=4326,
        null=True,
        blank=True,
        help_text="User's registered location"
    )
    district = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    
    # Security tracking
    failed_verification_attempts = models.IntegerField(default=0)
    failed_pin_attempts = models.IntegerField(default=0)
    transaction_pin = models.CharField(max_length=128, blank=True, null=True)  # Hashed
    
    # Preferences
    preferred_language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.ENGLISH,
        help_text="Preferred language for SMS notifications"
    )
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Use phone as the username field
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'accounts_user'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['role', 'is_verified']),
            models.Index(fields=['trust_score']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"
    
    def update_trust_score(self, delta):
        """Update trust score by delta."""
        self.trust_score = max(
            settings.TRUST_SCORE_MIN,
            min(settings.TRUST_SCORE_MAX, self.trust_score + delta)
        )
        self.save(update_fields=['trust_score'])
    
    def increment_verification_attempts(self):
        """Increment failed verification attempts and lock if exceeded."""
        self.failed_verification_attempts += 1
        if self.failed_verification_attempts >= settings.MAX_VERIFICATION_ATTEMPTS:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
        self.save(update_fields=['failed_verification_attempts', 'is_locked', 'locked_until'])
    
    def reset_verification_attempts(self):
        """Reset failed verification attempts."""
        self.failed_verification_attempts = 0
        self.save(update_fields=['failed_verification_attempts'])
    
    def increment_pin_attempts(self):
        """Increment failed PIN attempts and lock if exceeded."""
        self.failed_pin_attempts += 1
        if self.failed_pin_attempts >= settings.MAX_PIN_ATTEMPTS:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(hours=1)
        self.save(update_fields=['failed_pin_attempts', 'is_locked', 'locked_until'])
    
    def reset_pin_attempts(self):
        """Reset failed PIN attempts."""
        self.failed_pin_attempts = 0
        self.save(update_fields=['failed_pin_attempts'])
    
    @property
    def is_active_verified(self):
        """Check if user is active and verified."""
        return self.is_active and self.is_verified and not self.is_blacklisted and not self.is_locked
