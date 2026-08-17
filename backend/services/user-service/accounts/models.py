"""
================================================================================
CUSTOM USER MODEL FOR AGRICONNECT
================================================================================

This file defines the User model for AgriConnect.

Why a custom User model?
1. Use phone number as the primary identifier (not username)
2. Add custom fields (NRC, trust_score, location, etc.)
3. Support 4 user roles (Farmer, Buyer, Transporter, Admin)
4. Encrypt sensitive data (NRC numbers)
5. Track user verification status
6. Store location data (GPS coordinates)

The model extends Django's AbstractUser which provides:
- Password hashing
- Authentication methods
- Group/permissions support
- Built-in validation
================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================
# models: Django's ORM for database tables
# AbstractUser: Base user model we extend
# PointField: PostGIS field for storing GPS coordinates
# MinValueValidator, MaxValueValidator: Validate trust score range
# timezone: For timezone-aware datetime handling
# PhoneNumberField: Validates and formats phone numbers
# EncryptedCharField: Encrypts data at rest (NRC numbers)
# settings: Access to Django settings (trust score defaults)
# UserRole, Language: Our custom enums for roles and languages
# ============================================================================
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db.models import PointField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from fernet_fields import EncryptedCharField
from django.conf import settings
from shared.models.enums import UserRole, Language


class User(AbstractUser):
    """
    ===========================================================================
    CUSTOM USER MODEL
    ===========================================================================
    
    This is the main User model for AgriConnect.
    
    Why extend AbstractUser?
    - AbstractUser already has: password, last_login, is_active, etc.
    - We add custom fields on top of that
    - We remove username and use phone instead
    
    The model handles:
    1. Authentication (phone + password)
    2. Role-based access (Farmer, Buyer, Transporter, Admin)
    3. Trust scoring (reputation system)
    4. NRC encryption (security)
    5. Location tracking (GPS coordinates)
    6. Verification status
    7. Security locks (for failed attempts)
    
    ===========================================================================
    """
    
    # ========================================================================
    # REMOVE USERNAME - Use Phone Instead
    # ========================================================================
    # Django's default User model uses username as the primary identifier.
    # We don't want that because:
    # 1. Farmers in Zambia may not have email or usernames
    # 2. Phone numbers are unique and easy to remember
    # 3. SMS/USSD authentication works with phone numbers
    # 4. Phone numbers are already verified in Zambia
    #
    # Setting username = None removes the username field.
    # We'll use phone as USERNAME_FIELD instead.
    # ========================================================================
    username = None
    
    # ========================================================================
    # OVERRIDE FIELDS FROM AbstractUser
    # ========================================================================
    # AbstractUser has first_name and last_name as optional fields.
    # We make them required for better identification.
    # email is optional (not everyone has email in Zambia).
    # ========================================================================
    first_name = models.CharField(
        max_length=150,
        help_text="User's first name (required)"
    )
    last_name = models.CharField(
        max_length=150,
        help_text="User's last name (required)"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email address (optional)"
    )
    
    # ========================================================================
    # CORE FIELDS - Phone and NRC
    # ========================================================================
    # phone: Primary identifier for the user.
    #   - Uses PhoneNumberField for validation
    #   - Ensures phone numbers are in E.164 format (+260...)
    #   - Must be unique (no two users with same phone)
    #   - This is how users log in and receive SMS
    #
    # nrc: National Registration Card number (Zambian ID).
    #   - Encrypted at rest using Fernet symmetric encryption
    #   - Cannot be read directly from database
    #   - Required for KYC (Know Your Customer) compliance
    #   - Used for identity verification
    # ========================================================================
    phone = PhoneNumberField(
        unique=True,
        help_text="Phone number in E.164 format (e.g., +260...)"
    )
    nrc = EncryptedCharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="National Registration Card number (encrypted at rest)"
    )
    
    # ========================================================================
    # ROLE - What the user can do
    # ========================================================================
    # Each user has a role that determines their permissions.
    # 
    # FARMER: Can list produce, accept bids, receive payments
    # BUYER: Can search listings, place bids, make payments
    # TRANSPORTER: Can accept deliveries, update status, track GPS
    # ADMIN: Can moderate listings, resolve disputes, view analytics
    #
    # Uses UserRole enum from shared/models/enums.py
    # This ensures consistency across all services.
    # ========================================================================
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.FARMER,
        help_text="User's role in the system (Farmer, Buyer, Transporter, Admin)"
    )
    
    # ========================================================================
    # VERIFICATION AND SECURITY
    # ========================================================================
    # is_verified: User has verified their phone and NRC.
    #   - Verified users can list produce and place bids
    #   - Unverified users have limited functionality
    #   - Verification requires OTP + NRC check
    #
    # is_blacklisted: User has been banned from the platform.
    #   - Set by admin for fraud or policy violations
    #   - Blacklisted users cannot use the platform
    #   - Can be reversed by admin if mistake
    #
    # is_locked: User is temporarily locked out.
    #   - Happens after too many failed verification attempts
    #   - Also after too many failed PIN attempts
    #   - locked_until stores when they can try again
    #   - Auto-unlocks after timeout
    #
    # locked_until: When the lock expires.
    #   - If None, user is not locked
    #   - If date/time in future, user is locked until then
    # ========================================================================
    is_verified = models.BooleanField(
        default=False,
        help_text="Phone and NRC verified (true = verified)"
    )
    is_blacklisted = models.BooleanField(
        default=False,
        help_text="User is blacklisted (true = banned from platform)"
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="User is temporarily locked out (true = locked)"
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the lock expires (if locked)"
    )
    
    # ========================================================================
    # TRUST SCORE - Reputation System
    # ========================================================================
    # Trust score measures how trustworthy a user is.
    # 
    # Starts at 50 (neutral).
    # Goes up when:
    #   - Completed transactions (+5)
    #   - Good ratings from other users (+10)
    #   - Verified identity (+20)
    #
    # Goes down when:
    #   - Bad ratings from other users (-15)
    #   - Fraud alerts (-50)
    #   - Disputed transactions (-20)
    #
    # Range: -100 (very untrustworthy) to 100 (very trustworthy)
    # ========================================================================
    trust_score = models.IntegerField(
        default=settings.TRUST_SCORE_STARTING,
        validators=[
            MinValueValidator(settings.TRUST_SCORE_MIN),
            MaxValueValidator(settings.TRUST_SCORE_MAX)
        ],
        help_text="User trust score (-100 to 100)"
    )
    
    # ========================================================================
    # LOCATION - PostGIS Spatial Data
    # ========================================================================
    # location: GPS coordinates of the user.
    #   - Stored as PostGIS Point (longitude, latitude)
    #   - Used for distance-based searches
    #   - Helps find nearby listings
    #   - Requires PostgreSQL with PostGIS extension
    #
    # district: Text name of the district.
    #   - e.g., 'Lusaka', 'Mkushi', 'Kabwe'
    #   - Used for filtering by district
    #   - Helps with price index by district
    #
    # province: Text name of the province.
    #   - e.g., 'Lusaka Province', 'Central Province'
    #   - Used for regional filtering
    # ========================================================================
    location = PointField(
        srid=4326,  # WGS 84 (GPS coordinate system)
        null=True,
        blank=True,
        help_text="GPS coordinates (longitude, latitude)"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        help_text="District name (e.g., 'Lusaka', 'Mkushi')"
    )
    province = models.CharField(
        max_length=100,
        blank=True,
        help_text="Province name (e.g., 'Lusaka Province')"
    )
    
    # ========================================================================
    # SECURITY TRACKING
    # ========================================================================
    # failed_verification_attempts: Count of failed OTP attempts.
    #   - Incremented on each failed verification
    #   - Resets on successful verification
    #   - Locks account after MAX_VERIFICATION_ATTEMPTS
    #
    # failed_pin_attempts: Count of failed PIN attempts.
    #   - Incremented on each failed transaction PIN entry
    #   - Resets on successful PIN entry
    #   - Locks account after MAX_PIN_ATTEMPTS
    #
    # transaction_pin: User's 4-digit transaction PIN.
    #   - Hashed (not stored in plaintext)
    #   - Required for payment confirmation
    #   - 4 digits for easy memorization
    # ========================================================================
    failed_verification_attempts = models.IntegerField(default=0)
    failed_pin_attempts = models.IntegerField(default=0)
    transaction_pin = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Hashed 4-digit transaction PIN"
    )
    
    # ========================================================================
    # PREFERENCES
    # ========================================================================
    # preferred_language: Language for SMS notifications.
    #   - Supports: English, Nyanja, Bemba, Tonga, Lozi
    #   - Farmers receive SMS in their preferred language
    #   - Improves user experience
    #   - Defaults to English
    # ========================================================================
    preferred_language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.ENGLISH,
        help_text="Preferred language for SMS notifications"
    )
    
    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    # date_joined: When the user registered.
    #   - Set manually instead of auto_now_add
    #   - Allows us to set custom dates if needed
    #   - Used for analytics and reporting
    #
    # last_active: Last time the user did something.
    #   - Auto-updated on every save (auto_now=True)
    #   - Used to track active users
    #   - Used for engagement metrics
    #
    # verified_at: When the user was verified.
    #   - Set when NRC and phone are verified
    #   - Null if not verified yet
    #   - Used for compliance and auditing
    # ========================================================================
    date_joined = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user was verified (null if not verified)"
    )
    
    # ========================================================================
    # DJANGO REQUIRED FIELDS
    # ========================================================================
    # USERNAME_FIELD: The field used for authentication.
    #   - We use 'phone' instead of 'username'
    #   - Users log in with their phone number
    #
    # REQUIRED_FIELDS: Fields required when creating a user.
    #   - First name and last name are required
    #   - Everything else is optional or has defaults
    # ========================================================================
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # ========================================================================
    # METADATA (Meta Class)
    # ========================================================================
    # db_table: Name of the database table.
    #   - 'accounts_user' is clear and descriptive
    #   - Follows Django's naming convention
    #
    # indexes: Database indexes for faster queries.
    #   - phone index: Used for authentication lookups
    #   - role and is_verified index: Used for filtering
    #   - trust_score index: Used for sorting users
    #
    # ordering: Default ordering for queries.
    #   - Newest users first (most recent signups)
    #   - '-' means descending order
    # ========================================================================
    class Meta:
        db_table = 'accounts_user'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['role', 'is_verified']),
            models.Index(fields=['trust_score']),
        ]
        ordering = ['-created_at']  # Newest first
    
    # ========================================================================
    # STRING REPRESENTATION
    # ========================================================================
    # This is what shows in the admin interface and when printing.
    # Format: "John Doe (+260971234567)"
    # Makes it easy to identify users.
    # ========================================================================
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"
    
    # ========================================================================
    # TRUST SCORE METHODS
    # ========================================================================
    def update_trust_score(self, delta):
        """
        Update the user's trust score by delta amount.
        
        Example:
            user.update_trust_score(10)  # Adds 10 points
            user.update_trust_score(-15) # Subtracts 15 points
        
        Args:
            delta (int): Amount to add/subtract
        
        Returns:
            None (saves directly to database)
        
        Why:
            - Centralizes trust score logic
            - Ensures score stays within bounds (-100 to 100)
            - Easy to audit score changes
        """
        # Calculate new score, keeping within bounds
        new_score = self.trust_score + delta
        self.trust_score = max(
            settings.TRUST_SCORE_MIN,
            min(settings.TRUST_SCORE_MAX, new_score)
        )
        # Save only the trust_score field (performance optimization)
        self.save(update_fields=['trust_score'])
    
    # ========================================================================
    # VERIFICATION ATTEMPTS METHODS
    # ========================================================================
    def increment_verification_attempts(self):
        """
        Increment failed verification attempts and lock if exceeded.
        
        Called when a user enters an incorrect OTP code.
        
        Logic:
            1. Increment the counter
            2. If counter >= MAX_VERIFICATION_ATTEMPTS (5):
               - Lock the account
               - Set lock expiry time (30 minutes)
        
        Why:
            - Prevents brute force attacks on OTP codes
            - Gives users a cooling-off period
            - Alert admin of suspicious activity
        """
        self.failed_verification_attempts += 1
        if self.failed_verification_attempts >= settings.MAX_VERIFICATION_ATTEMPTS:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(
                minutes=settings.ACCOUNT_LOCKOUT_MINUTES
            )
        # Save only the changed fields
        self.save(update_fields=['failed_verification_attempts', 'is_locked', 'locked_until'])
    
    def reset_verification_attempts(self):
        """
        Reset failed verification attempts.
        
        Called when:
            1. User successfully verifies
            2. Account lock expires
            3. Admin manually resets
        
        Why:
            - Allows user to try again after success
            - Resets the lockout counter
        """
        self.failed_verification_attempts = 0
        self.save(update_fields=['failed_verification_attempts'])
    
    # ========================================================================
    # PIN ATTEMPTS METHODS
    # ========================================================================
    def increment_pin_attempts(self):
        """
        Increment failed PIN attempts and lock if exceeded.
        
        Called when a user enters an incorrect transaction PIN.
        
        Logic:
            1. Increment the counter
            2. If counter >= MAX_PIN_ATTEMPTS (3):
               - Lock the account
               - Set lock expiry time (1 hour)
               - PIN lockout is stricter than verification
        
        Why:
            - Transaction PIN is for payments (higher security)
            - 3 attempts before lockout
            - 1 hour lockout (longer than verification)
        """
        self.failed_pin_attempts += 1
        if self.failed_pin_attempts >= settings.MAX_PIN_ATTEMPTS:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(hours=1)
        self.save(update_fields=['failed_pin_attempts', 'is_locked', 'locked_until'])
    
    def reset_pin_attempts(self):
        """
        Reset failed PIN attempts.
        
        Called when:
            1. User successfully enters correct PIN
            2. Account lock expires
            3. Admin manually resets
        
        Why:
            - Allows user to try again after success
            - Resets the lockout counter
        """
        self.failed_pin_attempts = 0
        self.save(update_fields=['failed_pin_attempts'])
    
    # ========================================================================
    # PROPERTY - Active and Verified
    # ========================================================================
    @property
    def is_active_verified(self):
        """
        Check if user is active and verified.
        
        Returns:
            bool: True if user is:
                - Active (not deactivated)
                - Verified (phone and NRC)
                - Not blacklisted
                - Not locked
        
        Why:
            - Quick check for permissions
            - Used in multiple places
            - Consistent logic across the app
        """
        return (
            self.is_active and           # User account is active
            self.is_verified and         # User has verified phone and NRC
            not self.is_blacklisted and  # User is not banned
            not self.is_locked           # User is not locked out
        )
