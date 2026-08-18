"""
Serializers for the User Service.

These convert User models to/from JSON for the API.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from phonenumber_field.serializerfields import PhoneNumberField

# Import from local enums (NOT shared)
from .enums import UserRole

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles:
    - Phone number validation (unique)
    - Password validation (strength)
    - User creation with hashed password
    """
    phone = PhoneNumberField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    role = serializers.ChoiceField(
        choices=UserRole.choices,
        default=UserRole.FARMER,
        required=False
    )
    
    class Meta:
        model = User
        fields = ['phone', 'first_name', 'last_name', 'email', 'password', 'role']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': False, 'allow_blank': True},
        }
    
    def validate_phone(self, value):
        """Ensure phone number is unique."""
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value
    
    def validate_password(self, value):
        """Ensure password meets security requirements."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def create(self, validated_data):
        """Create a new user with hashed password."""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user data.
    
    Used for GET requests (viewing user profiles).
    Does NOT show password.
    """
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'first_name', 'last_name', 'email',
            'role', 'role_display', 'is_verified', 'trust_score',
            'district', 'province', 'latitude', 'longitude',
            'preferred_language', 'created_at', 'last_active', 'verified_at',
        ]
        read_only_fields = [
            'id', 'is_verified', 'trust_score',
            'created_at', 'last_active', 'verified_at',
        ]
    
    def get_latitude(self, obj):
        """Extract latitude from PostGIS Point."""
        if obj.location:
            return obj.location.y
        return None
    
    def get_longitude(self, obj):
        """Extract longitude from PostGIS Point."""
        if obj.location:
            return obj.location.x
        return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profiles.
    
    Used for PATCH requests (partial updates).
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'district', 'province', 'preferred_language']
    
    def validate_email(self, value):
        """Ensure email is unique (if provided)."""
        if value:
            if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "A user with this email already exists."
                )
        return value


class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    
    Used for:
    - POST /api/v1/auth/verify-otp/
    - POST /api/v1/auth/resend-otp/
    """
    phone = PhoneNumberField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    purpose = serializers.ChoiceField(
        choices=[
            ('phone_verification', 'Phone Verification'),
            ('login', 'Login'),
            ('password_reset', 'Password Reset'),
        ],
        required=True
    )
    
    def validate_phone(self, value):
        """Ensure user exists with this phone."""
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "No user found with this phone number."
            )
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    
    Used for:
    - POST /api/v1/auth/change-password/
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        """Validate that new passwords match and are strong."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        try:
            validate_password(data['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError(
                {"new_password": e.messages}
            )
        return data
