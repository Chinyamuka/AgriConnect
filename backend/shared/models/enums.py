"""
Enums for AgriConnect - Single source of truth for all constants.

Why enums?
1. Prevent typos (e.g., 'framer' vs 'farmer')
2. IDE autocomplete works
3. Single source of truth
4. Easy to add new values later
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


class ListingStatus(models.TextChoices):
    """
    Status of a produce listing.
    
    Lifecycle: ACTIVE → PENDING_REVIEW → SOLD/EXPIRED
    """
    ACTIVE = "active", "Active"                    # Available for bidding
    SOLD = "sold", "Sold"                          # Sold to a buyer
    EXPIRED = "expired", "Expired"                # 14 days passed
    PENDING_REVIEW = "pending", "Pending Review"  # Awaiting admin approval
    FLAGGED = "flagged", "Flagged"                # Suspicious activity


class DeliveryStatus(models.TextChoices):
    """
    Status of a delivery (for Transporter role).
    
    Lifecycle: PENDING → PICKED_UP → IN_TRANSIT → DELIVERED
    """
    PENDING = "pending", "Pending"                # Awaiting transporter
    PICKED_UP = "picked_up", "Picked Up"          # Farmer handed over
    IN_TRANSIT = "in_transit", "In Transit"       # On the way
    DELIVERED = "delivered", "Delivered"          # Buyer received
    FAILED = "failed", "Failed"                   # Delivery failed


class BidStatus(models.TextChoices):
    """
    Status of a bid.
    
    Lifecycle: PENDING → ACCEPTED/REJECTED
    """
    PENDING = "pending", "Pending"                # Awaiting farmer response
    ACCEPTED = "accepted", "Accepted"            # Farmer accepted
    REJECTED = "rejected", "Rejected"            # Farmer rejected
    WITHDRAWN = "withdrawn", "Withdrawn"          # Buyer withdrew


class PaymentStatus(models.TextChoices):
    """
    Status of payment and escrow.
    
    Lifecycle: INITIATED → PENDING → PAID_ESCROW → DELIVERED → COMPLETED
    """
    INITIATED = "initiated", "Initiated"          # Payment started
    PENDING = "pending", "Pending"                # Awaiting payment
    PROCESSING = "processing", "Processing"       # With Flutterwave
    PAID_ESCROW = "escrow", "Paid to Escrow"     # Funds held safely
    DELIVERED = "delivered", "Delivered"          # Goods delivered
    COMPLETED = "completed", "Completed"          # Funds released
    REFUNDED = "refunded", "Refunded"            # Money returned
    FAILED = "failed", "Failed"                   # Payment failed


class TransactionType(models.TextChoices):
    """
    Types of money movements.
    """
    PAYMENT = "payment", "Payment"                # Buyer pays
    PAYOUT = "payout", "Payout"                   # Farmer receives
    REFUND = "refund", "Refund"                   # Money back to buyer
    FEE = "fee", "Platform Fee"                  # AgriConnect fee
    DELIVERY = "delivery", "Delivery Fee"         # Transporter payment


class FraudSeverity(models.TextChoices):
    """
    How serious is a fraud alert?
    """
    LOW = "low", "Low"                            # Minor concern
    MEDIUM = "medium", "Medium"                  # Needs review
    HIGH = "high", "High"                        # Likely fraud
    CRITICAL = "critical", "Critical"            # Immediate action


class Language(models.TextChoices):
    """
    SMS language support for Zambia.
    
    Farmers in different regions speak different languages.
    We support the 4 main local languages.
    """
    ENGLISH = "en", "English"
    NYANJA = "ny", "Nyanja"
    BEMBA = "bem", "Bemba"
    TONGA = "toi", "Tonga"
    LOZI = "loz", "Lozi"
