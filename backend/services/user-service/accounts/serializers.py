"""
================================================================================
SERIALIZERS FOR USER API
================================================================================

This file defines how User objects are converted to/from JSON.

What are serializers?
1. Convert Django models to JSON (for API responses)
2. Convert JSON to Django models (for API requests)
3. Validate incoming data (ensure data is correct)
4. Handle password hashing (security)

Why do we need serializers?
- Django REST Framework uses them for API responses
- They ensure data is in the right format
- They validate data before saving to database
- They handle nested relationships

Example flow:
1. User registers (sends JSON to /api/auth/register/)
2. Serializer validates the data
3. Serializer creates a User object
4. User is saved to database
5. Serializer returns the user data as JSON
================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================
# serializers: Django REST Framework's serializer base class
# ModelSerializer: Automatically creates serializers from models
# get_user_model: Gets the current user model (accounts.User)
# UserRole: Our enum for user roles
# ============================================================================
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from phonenumber_field.serializerfields import PhoneNumberField
from shared.models.enums import UserRole

# Get the custom User model
User = get_user_model()


# ============================================================================
# USER REGISTRATION SERIALIZER
# ============================================================================
# This serializer handles user registration (signup).
# It validates the data and creates a new user.
#
# Fields handled:
#   - phone: Validates phone number format
#   - first_name: Required, max length 150
#   - last_name: Required, max length 150
#   - password: Validated for strength, hashed before saving
#   - role: Optional, defaults to FARMER
# ============================================================================
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    This is used when a new user signs up.
    It validates the data and creates a new user.
    
    Why separate from UserSerializer?
    - Registration has different requirements (password required)
    - Registration creates new users
    - UserSerializer is for displaying user data
    """
    
    # ========================================================================
    # CUSTOM FIELDS
    # ========================================================================
    # phone: Uses PhoneNumberField for validation
    #   - Ensures phone is in E.164 format (+260...)
    #   - Validates the phone number exists
    #
    # password: Uses CharField with write_only=True
    #   - write_only: Password is never sent back in responses
    #   - style={'input_type': 'password'}: Shows as password field in browsable API
    #
    # role: ChoiceField with UserRole choices
    #   - Optional, defaults to FARMER
    # ========================================================================
    phone = PhoneNumberField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password (min 8 characters)"
    )
    role = serializers.ChoiceField(
        choices=UserRole.choices,
        default=UserRole.FARMER,
        required=False,
        help_text="User role: farmer, buyer, transporter, admin"
    )
    
    class Meta:
        model = User
        fields = [
            'phone',
            'first_name',
            'last_name',
            'email',
            'password',
            'role',
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': False, 'allow_blank': True},
        }
    
    # ========================================================================
    # FIELD VALIDATION - Phone
    # ========================================================================
    def validate_phone(self, value):
        """
        Validate the phone number is unique.
        
        Why:
            - Each user must have a unique phone number
            - Prevents duplicate accounts
            - Phone is the primary identifier
        
        Args:
            value: Phone number to validate
        
        Returns:
            The validated phone number
        
        Raises:
            serializers.ValidationError: If phone already exists
        """
        # Check if a user with this phone already exists
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value
    
    # ========================================================================
    # FIELD VALIDATION - Password
    # ========================================================================
    def validate_password(self, value):
        """
        Validate the password meets security requirements.
        
        Why:
            - Ensures users have strong passwords
            - Uses Django's built-in password validators
            - Prevents common weak passwords
        
        Args:
            value: Password to validate
        
        Returns:
            The validated password
        
        Raises:
            serializers.ValidationError: If password is weak
        """
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    # ========================================================================
    # CREATE METHOD - How to create a new user
    # ========================================================================
    def create(self, validated_data):
        """
        Create a new user with the validated data.
        
        Why use create_user instead of User.objects.create?
            - create_user hashes the password automatically
            - create_user handles the password correctly
            - Using create_user is more secure
        
        Args:
            validated_data: The validated registration data
        
        Returns:
            User: The newly created user
        
        Note:
            - 'password' is removed from validated_data before creating user
            - create_user handles password hashing
        """
        # Remove password from data (it's handled separately)
        password = validated_data.pop('password')
        
        # Create the user with the remaining data
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


# ============================================================================
# USER SERIALIZER - For displaying user data
# ============================================================================
# This serializer is used for GET requests (viewing user data).
# It shows user information but does NOT show the password.
#
# Fields displayed:
#   - id: User UUID
#   - phone: Phone number
#   - first_name: First name
#   - last_name: Last name
#   - email: Email address
#   - role: User role
#   - is_verified: Verification status
#   - trust_score: Reputation score
#   - district: District name
#   - province: Province name
#   - preferred_language: Language preference
#   - created_at: Registration date
#   - last_active: Last activity
# ============================================================================
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user data.
    
    This is used for:
        - GET /api/users/me (current user profile)
        - GET /api/users/{id} (other user profile)
        - GET /api/users/ (list of users)
    """
    
    # ========================================================================
    # CUSTOM FIELD - Role Display
    # ========================================================================
    # role_display: Shows the human-readable role name.
    #   - Example: 'farmer' -> 'Farmer'
    #   - Uses get_role_display() method from the model
    #   - Useful for frontend display
    # ========================================================================
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True,
        help_text="Human-readable role name"
    )
    
    # ========================================================================
    # CUSTOM FIELD - Location
    # ========================================================================
    # latitude and longitude: Extract coordinates from PostGIS Point.
    #   - The location field is a PostGIS Point (x, y)
    #   - We extract x (longitude) and y (latitude)
    #   - Frontend needs separate lat/lng values
    #   - Read-only (users can't set location through API)
    # ========================================================================
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            # Identifier
            'id',
            
            # Contact info
            'phone',
            'first_name',
            'last_name',
            'email',
            
            # Role
            'role',
            'role_display',
            
            # Status
            'is_verified',
            'trust_score',
            
            # Location
            'district',
            'province',
            'latitude',
            'longitude',
            
            # Preferences
            'preferred_language',
            
            # Timestamps
            'created_at',
            'last_active',
            'verified_at',
        ]
        read_only_fields = [
            'id',
            'is_verified',
            'trust_score',
            'created_at',
            'last_active',
            'verified_at',
        ]
    
    # ========================================================================
    # GETTER METHOD - Latitude
    # ========================================================================
    def get_latitude(self, obj):
        """
        Get the latitude from the PostGIS Point.
        
        Args:
            obj: User object
        
        Returns:
            float: Latitude coordinate, or None if no location
        """
        if obj.location:
            # PostGIS Point stores (x, y) = (longitude, latitude)
            return obj.location.y  # y = latitude
        return None
    
    # ========================================================================
    # GETTER METHOD - Longitude
    # ========================================================================
    def get_longitude(self, obj):
        """
        Get the longitude from the PostGIS Point.
        
        Args:
            obj: User object
        
        Returns:
            float: Longitude coordinate, or None if no location
        """
        if obj.location:
            # PostGIS Point stores (x, y) = (longitude, latitude)
            return obj.location.x  # x = longitude
        return None


# ============================================================================
# USER PROFILE UPDATE SERIALIZER
# ============================================================================
# This serializer handles updating user profiles.
# It allows users to update their information.
#
# Fields that can be updated:
#   - first_name
#   - last_name
#   - email
#   - district
#   - province
#   - preferred_language
#
# Fields that cannot be updated through API:
#   - phone (must be changed through verification process)
#   - role (must be changed by admin)
#   - trust_score (system-managed)
# ============================================================================
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profiles.
    
    This is used for:
        - PATCH /api/users/me (update current user)
        - PATCH /api/users/{id} (admin update)
    
    Note:
        - Only allows updating safe fields
        - Doesn't allow changing phone or role
    """
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'district',
            'province',
            'preferred_language',
        ]
    
    # ========================================================================
    # FIELD VALIDATION - Email
    # ========================================================================
    def validate_email(self, value):
        """
        Validate email format if provided.
        
        Why:
            - Email is optional but should be valid if provided
            - Django's EmailField validation is already applied
            - We just need to check uniqueness if updating
        
        Args:
            value: Email to validate
        
        Returns:
            The validated email
        
        Raises:
            serializers.ValidationError: If email is already used
        """
        if value:
            # Check if another user has this email
            # Exclude the current user from the check
            if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "A user with this email already exists."
                )
        return value


# ============================================================================
# OTP VERIFICATION SERIALIZER
# ============================================================================
# This serializer handles OTP (One-Time Password) verification.
#
# Fields:
#   - phone: The user's phone number
#   - code: The 6-digit OTP code
#   - purpose: What the OTP is for (phone_verification, login, etc.)
# ============================================================================
class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    
    This is used for:
        - POST /api/auth/verify-otp/ (verify OTP code)
        - POST /api/auth/resend-otp/ (resend OTP)
    """
    
    phone = PhoneNumberField(required=True)
    code = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        help_text="6-digit OTP code"
    )
    purpose = serializers.ChoiceField(
        choices=[
            ('phone_verification', 'Phone Verification'),
            ('login', 'Login'),
            ('password_reset', 'Password Reset'),
        ],
        required=True,
        help_text="What the OTP is for"
    )
    
    # ========================================================================
    # FIELD VALIDATION - Phone exists
    # ========================================================================
    def validate_phone(self, value):
        """
        Validate the phone number exists.
        
        Why:
            - OTP is only sent to registered users
            - Prevents sending OTPs to non-existent users
        
        Args:
            value: Phone number to check
        
        Returns:
            The validated phone number
        
        Raises:
            serializers.ValidationError: If user doesn't exist
        """
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "No user found with this phone number."
            )
        return value


# ============================================================================
# CHANGE PASSWORD SERIALIZER
# ============================================================================
# This serializer handles password changes.
#
# Fields:
#   - old_password: Current password
#   - new_password: New password (validated)
#   - confirm_password: Must match new_password
# ============================================================================
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    
    This is used for:
        - POST /api/auth/change-password/ (change password)
    
    Why separate from profile update?
        - Password change has special security requirements
        - Requires old password verification
        - Requires password confirmation
    """
    
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Current password"
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="New password (min 8 characters)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirm new password"
    )
    
    # ========================================================================
    # FIELD VALIDATION - New password confirmation
    # ========================================================================
    def validate(self, data):
        """
        Validate that new password and confirmation match.
        
        Also validates password strength.
        
        Args:
            data: The validated data
        
        Returns:
            The validated data
        
        Raises:
            serializers.ValidationError: If passwords don't match or are weak
        """
        # Check if new password and confirmation match
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        
        # Validate password strength
        try:
            validate_password(data['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError(
                {"new_password": e.messages}
            )
        
        return data
