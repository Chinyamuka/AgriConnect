"""
================================================================================
ADMIN INTERFACE FOR USER MANAGEMENT
================================================================================

This file configures how users appear in Django's admin interface.

Why have an admin interface?
1. Administrators can manage users without writing code
2. View and edit user profiles
3. Verify or flag users
4. Resolve disputes
5. Monitor platform activity

Django's admin is powerful but needs configuration to work with our custom User model.
================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================
# admin: Django's admin registration
# UserAdmin: Default admin interface for users (we extend it)
# User: Our custom user model
# ============================================================================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    ===========================================================================
    CUSTOM ADMIN INTERFACE FOR USER MODEL
    ===========================================================================
    
    This class configures how users appear in the admin panel.
    We extend Django's default UserAdmin and customize it for our User model.
    
    Why extend UserAdmin?
    - UserAdmin already knows how to handle authentication
    - UserAdmin knows about password hashing
    - UserAdmin handles permissions and groups
    - We just add our custom fields and behaviors
    
    ===========================================================================
    """
    
    # ========================================================================
    # LIST DISPLAY - What columns show in the user list
    # ========================================================================
    # These are the columns displayed in the admin user list.
    # Order matters - they appear left to right.
    #
    # Fields shown:
    #   1. phone: The user's phone number (primary identifier)
    #   2. first_name: User's first name
    #   3. last_name: User's last name
    #   4. role: Farmer, Buyer, Transporter, or Admin
    #   5. is_verified: Whether user is verified
    #   6. trust_score: User's reputation score
    #   7. is_active: Whether account is active
    #
    # Why these fields?
    #   - Phone: Identifies the user
    #   - Name: Human-readable identification
    #   - Role: Shows what the user can do
    #   - Verified: Shows KYC status
    #   - Trust Score: Shows reputation
    #   - Active: Shows if account is enabled
    # ========================================================================
    list_display = (
        'phone',
        'first_name',
        'last_name',
        'role',
        'is_verified',
        'trust_score',
        'is_active',
    )
    
    # ========================================================================
    # LIST FILTER - Sidebar filters for the user list
    # ========================================================================
    # These create filter options in the right sidebar.
    # Administrators can click to filter users by these fields.
    #
    # Filters available:
    #   1. role: Show only farmers, buyers, etc.
    #   2. is_verified: Show verified or unverified users
    #   3. is_blacklisted: Show blacklisted users
    #   4. is_locked: Show locked out users
    #   5. is_active: Show active or inactive users
    #
    # Why these filters?
    #   - Administrators need to find specific user types
    #   - Quick access to problematic users (blacklisted, locked)
    #   - Monitor verification progress
    # ========================================================================
    list_filter = (
        'role',
        'is_verified',
        'is_blacklisted',
        'is_locked',
        'is_active',
    )
    
    # ========================================================================
    # SEARCH FIELDS - What administrators can search for
    # ========================================================================
    # These fields are searchable in the admin search bar.
    # Administrators can type a query and search these fields.
    #
    # Searchable fields:
    #   1. phone: Find user by phone number
    #   2. first_name: Find by first name
    #   3. last_name: Find by last name
    #   4. email: Find by email
    #
    # Why these fields?
    #   - Phone: Quick lookup by phone number
    #   - Name: Find users by name
    #   - Email: Find by email (if provided)
    # ========================================================================
    search_fields = (
        'phone',
        'first_name',
        'last_name',
        'email',
    )
    
    # ========================================================================
    # DEFAULT ORDERING
    # ========================================================================
    # How users are sorted by default in the admin list.
    # We use '-created_at' to show newest users first.
    # '-': Descending order (newest first)
    # ========================================================================
    ordering = ('-created_at',)
    
    # ========================================================================
    # FIELDSETS - How the user detail page is organized
    # ========================================================================
    # fieldsets group fields into sections on the user edit page.
    # This makes the admin interface cleaner and more organized.
    #
    # Each fieldset has:
    #   - title: Section header
    #   - fields: List of fields in that section
    #   - classes: CSS classes for styling
    #
    # Sections:
    #   1. Personal Info: User's basic information
    #   2. Role & Status: User's role and verification status
    #   3. Trust & Location: Reputation and location data
    #   4. Security: Security tracking fields
    #   5. Important dates: Timestamps
    # ========================================================================
    fieldsets = (
        # ====================================================================
        # SECTION 1: PERSONAL INFO
        # ====================================================================
        # These are the user's basic identifying information.
        # All users must have these fields.
        #
        # phone: The primary identifier (used for login)
        # password: Hashed password (admin can reset it)
        # first_name: User's first name
        # last_name: User's last name
        # email: Optional email address
        # nrc: National Registration Card (encrypted)
        # ====================================================================
        (_('Personal Info'), {
            'fields': (
                'phone',
                'password',
                'first_name',
                'last_name',
                'email',
                'nrc',
            )
        }),
        
        # ====================================================================
        # SECTION 2: ROLE & STATUS
        # ====================================================================
        # These fields determine what the user can do and their status.
        #
        # role: Farmer, Buyer, Transporter, or Admin
        # is_verified: Whether phone and NRC are verified
        # is_blacklisted: Whether user is banned
        # is_locked: Whether user is temporarily locked out
        # locked_until: When the lock expires
        # ====================================================================
        (_('Role & Status'), {
            'fields': (
                'role',
                'is_verified',
                'is_blacklisted',
                'is_locked',
                'locked_until',
            )
        }),
        
        # ====================================================================
        # SECTION 3: TRUST & LOCATION
        # ====================================================================
        # These fields track user reputation and location.
        #
        # trust_score: Reputation score (-100 to 100)
        # location: GPS coordinates (PostGIS Point)
        # district: District name
        # province: Province name
        # ====================================================================
        (_('Trust & Location'), {
            'fields': (
                'trust_score',
                'location',
                'district',
                'province',
            )
        }),
        
        # ====================================================================
        # SECTION 4: SECURITY
        # ====================================================================
        # These fields track security-related information.
        #
        # failed_verification_attempts: Count of failed OTP attempts
        # failed_pin_attempts: Count of failed PIN attempts
        # transaction_pin: Hashed 4-digit transaction PIN
        # ====================================================================
        (_('Security'), {
            'fields': (
                'failed_verification_attempts',
                'failed_pin_attempts',
                'transaction_pin',
            )
        }),
        
        # ====================================================================
        # SECTION 5: IMPORTANT DATES
        # ====================================================================
        # These fields track important timestamps.
        #
        # last_login: When user last logged in
        # date_joined: When user registered
        # verified_at: When user was verified
        # ====================================================================
        (_('Important Dates'), {
            'fields': (
                'last_login',
                'date_joined',
                'verified_at',
            )
        }),
    )
    
    # ========================================================================
    # ADD FIELDSETS - For creating new users
    # ========================================================================
    # This is the form shown when an administrator creates a new user.
    # It's simpler than the edit form and focuses on required fields.
    #
    # Fields required to create a user:
    #   1. phone: User's phone number (required, unique)
    #   2. first_name: First name (required)
    #   3. last_name: Last name (required)
    #   4. password1: Initial password
    #   5. password2: Confirm password
    #   6. role: User's role (default: Farmer)
    #
    # Why 'wide' class?
    #   - Makes the form wider for better readability
    # ========================================================================
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'role',
            ),
        }),
    )
    
    # ========================================================================
    # READONLY FIELDS - Cannot be edited by administrators
    # ========================================================================
    # These fields are displayed but cannot be changed in the admin.
    # They are set automatically by the system.
    #
    # Read-only fields:
    #   1. created_at: Set on creation
    #   2. updated_at: Auto-updated on save
    #   3. failed_verification_attempts: Managed by the system
    #   4. failed_pin_attempts: Managed by the system
    #
    # Why make them read-only?
    #   - Prevent accidental modification
    #   - Maintain data integrity
    #   - These should only be changed by the system logic
    # ========================================================================
    readonly_fields = (
        'created_at',
        'updated_at',
        'failed_verification_attempts',
        'failed_pin_attempts',
    )
    
    # ========================================================================
    # FILTER HORIZONTAL - For Many-to-Many fields
    # ========================================================================
    # These use a nicer widget for managing groups and permissions.
    # Instead of a multi-select box, it shows two columns:
    #   - Left: Available items
    #   - Right: Selected items
    #
    # This is much more user-friendly for administrators.
    # ========================================================================
    filter_horizontal = ('groups', 'user_permissions',)
