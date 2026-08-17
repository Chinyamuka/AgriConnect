"""
================================================================================
API VIEWS FOR USER SERVICE
================================================================================

This file defines all the API endpoints for user management.
"""
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models as django_models
from shared.models.enums import UserRole

from ..serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    OTPVerificationSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


# ============================================================================
# PERMISSION CLASSES
# ============================================================================
class IsAdminUser(permissions.BasePermission):
    """Custom permission: Only allow admin users."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == UserRole.ADMIN
        )


# ============================================================================
# REGISTRATION VIEW
# ============================================================================
class RegisterView(APIView):
    """User Registration Endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User created successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# LOGIN VIEW
# ============================================================================
class LoginView(APIView):
    """User Login Endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')
        
        if not phone or not password:
            return Response({
                'error': 'Phone and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, username=phone, password=password)
        
        if user is None:
            return Response({
                'error': 'Invalid phone number or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if user.is_locked:
            return Response({
                'error': f'Account is locked. Try again after {user.locked_until}'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if user.is_blacklisted:
            return Response({
                'error': 'Account has been blacklisted. Contact support.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user.last_active = timezone.now()
        user.save(update_fields=['last_active'])
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


# ============================================================================
# VERIFY OTP VIEW
# ============================================================================
class VerifyOTPView(APIView):
    """Verify OTP Endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        
        try:
            user = User.objects.get(phone=phone)
            
            # TODO: Check OTP in Redis
            # For demo: Accept any 6-digit code starting with '1'
            if code.startswith('1') and len(code) == 6:
                user.is_verified = True
                user.verified_at = timezone.now()
                user.reset_verification_attempts()
                user.save()
                
                return Response({
                    'message': 'OTP verified successfully',
                    'verified': True,
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            else:
                user.increment_verification_attempts()
                return Response({
                    'error': 'Invalid OTP code',
                    'attempts_remaining': 5 - user.failed_verification_attempts
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# RESEND OTP VIEW
# ============================================================================
class ResendOTPView(APIView):
    """Resend OTP Endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        
        if not phone:
            return Response({
                'error': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone=phone)
            
            # TODO: Generate and send OTP via Africa's Talking
            
            return Response({
                'message': 'OTP sent successfully',
                'sent': True
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# USER PROFILE VIEW
# ============================================================================
class UserProfileView(generics.RetrieveAPIView):
    """User Profile Endpoint."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


# ============================================================================
# UPDATE USER PROFILE VIEW
# ============================================================================
class UpdateUserProfileView(generics.UpdateAPIView):
    """Update User Profile Endpoint."""
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


# ============================================================================
# CHANGE PASSWORD VIEW
# ============================================================================
class ChangePasswordView(APIView):
    """Change Password Endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        if not user.check_password(old_password):
            return Response({
                'error': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


# ============================================================================
# USER LIST VIEW - Admin Only
# ============================================================================
class UserListView(generics.ListAPIView):
    """User List Endpoint - Admin Only."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            is_verified_bool = is_verified.lower() == 'true'
            queryset = queryset.filter(is_verified=is_verified_bool)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                django_models.Q(first_name__icontains=search) |
                django_models.Q(last_name__icontains=search) |
                django_models.Q(phone__icontains=search)
            )
        
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset


# ============================================================================
# USER DETAIL VIEW - Admin Only
# ============================================================================
class UserDetailView(generics.RetrieveAPIView):
    """User Detail Endpoint - Admin Only."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = User.objects.all()
    lookup_field = 'id'
