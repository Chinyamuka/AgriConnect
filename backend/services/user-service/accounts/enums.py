"""
Enums for the User Service.

These are local enums that define:
1. User roles (Farmer, Buyer, Transporter, Admin)
2. Supported languages (English, Nyanja, Bemba, Tonga, Lozi)

Why local enums?
- Each service should have its own enums
- Avoids dependency on a shared module
- Easier to maintain and extend
- Consistent across the service
"""
from django.db import models


class UserRole(models.TextChoices):
    """
    The 4 user roles in AgriConnect.
    
    Each role has different permissions and capabilities.
    """
    FARMER = "farmer", "Farmer"
    BUYER = "buyer", "Buyer"
    TRANSPORTER = "transporter", "Transporter"
    ADMIN = "admin", "Administrator"


class Language(models.TextChoices):
    """
    Supported languages for SMS notifications.
    
    Zambia has 72+ languages. We support the 4 most common:
    - English (official language)
    - Nyanja (spoken in Eastern Province)
    - Bemba (spoken in Northern Province)
    - Tonga (spoken in Southern Province)
    - Lozi (spoken in Western Province)
    """
    ENGLISH = "en", "English"
    NYANJA = "ny", "Nyanja"
    BEMBA = "bem", "Bemba"
    TONGA = "toi", "Tonga"
    LOZI = "loz", "Lozi"


# Aliases for backward compatibility
UserRoles = UserRole
Languages = Language
