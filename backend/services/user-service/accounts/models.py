"""
Custom User model for AgriConnect.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.gis.db.models import PointField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from encrypted_model_fields.fields import EncryptedCharField
from django.conf import settings

# Import from local enums
from .enums import UserRole, Language


# ============================================================================
# CUSTOM USER MANAGER
# ============================================================================
class UserManager(BaseUserManager):
    """
    Custom user manager that uses phone instead of username.
    
    Django's default UserManager expects a username field.
    Since we use phone as the USERNAME_FIELD, we need to override
    the manager to handle this correctly.
    """
    
    def create_user(self, phone, password=None, **extra_fields):
        """
        Create and save a user with the given phone and password.
        
        Args:
            phone: The user's phone number (required)
            password: The user's password (optional)
            extra_fields: Additional fields like first_name, last_name, etc.
        
        Returns:
            User: The created user
        """
        if not phone:
            raise ValueError('The Phone number must be set')
        
        # Create the user with phone as the identifier
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, password=None, **extra_fields):
        """
        Create and save a superuser with the given phone and password.
        
        Args:
            phone: The user's phone number (required)
            password: The user's password (required)
            extra_fields: Additional fields
        
        Returns:
            User: The created superuser
        """
        # Set default permissions for superuser
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        
        # Ensure the superuser has admin role
        extra_fields.setdefault('role', UserRole.ADMIN)
        
        return self.create_user(phone, password, **extra_fields)


# ============================================================================
# USER MODEL
# ============================================================================
class User(AbstractUser):
    """
    Custom User model with phone as primary identifier.
    """
    # Remove username field
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
    
    # Role
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.FARMER,
        help_text="User's role in the system"
    )
    
    # Verification and security
    is_verified = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Trust score
    trust_score = models.IntegerField(
        default=settings.TRUST_SCORE_STARTING,
        validators=[
            MinValueValidator(settings.TRUST_SCORE_MIN),
            MaxValueValidator(settings.TRUST_SCORE_MAX)
        ]
    )
    
    # Location
    location = PointField(
        srid=4326,
        null=True,
        blank=True
    )
    district = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    
    # Security tracking
    failed_verification_attempts = models.IntegerField(default=0)
    failed_pin_attempts = models.IntegerField(default=0)
    transaction_pin = models.CharField(max_length=128, blank=True, null=True)
    
    # Preferences
    preferred_language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.ENGLISH
    )
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use phone as the username field
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Use the custom manager
    objects = UserManager()
    
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
        new_score = self.trust_score + delta
        self.trust_score = max(
            settings.TRUST_SCORE_MIN,
            min(settings.TRUST_SCORE_MAX, new_score)
        )
        self.save(update_fields=['trust_score'])
    
    def increment_verification_attempts(self):
        self.failed_verification_attempts += 1
        if self.failed_verification_attempts >= settings.MAX_VERIFICATION_ATTEMPTS:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(
                minutes=settings.ACCOUNT_LOCKOUT_MINUTES
            )
        self.save(update_fields=['failed_verification_attempts', 'is_locked', 'locked_until'])
    
    def reset_verification_attempts(self):
        self.failed_verification_attempts = 0
        self.save(update_fields=['failed_verification_attempts'])
    
    def increment_pin_attempts(self):
        self.failed_pin_attempts += 1
        if self.failed_pin_attempts >= settings.MAX_PIN_ATTEMPTS:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(hours=1)
        self.save(update_fields=['failed_pin_attempts', 'is_locked', 'locked_until'])
    
    def reset_pin_attempts(self):
        self.failed_pin_attempts = 0
        self.save(update_fields=['failed_pin_attempts'])
    
    @property
    def is_active_verified(self):
        return (
            self.is_active and
            self.is_verified and
            not self.is_blacklisted and
            not self.is_locked
        )
