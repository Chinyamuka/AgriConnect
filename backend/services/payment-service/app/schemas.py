"""
================================================================================
PYDANTIC SCHEMAS FOR PAYMENT SERVICE
================================================================================
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment status."""
    INITIATED = "initiated"
    PENDING = "pending"
    PROCESSING = "processing"
    PAID_ESCROW = "paid_escrow"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    """Supported payment methods."""
    AIRTEL_MONEY = "airtel_money"
    MTN_MOMO = "mtn_momo"
    ZAMTEL_KWACHA = "zamtel_kwacha"
    CARD = "card"


class PaymentInitiateRequest(BaseModel):
    """Request to initiate a payment."""
    bid_id: UUID = Field(..., description="ID of the bid being paid for")
    amount: float = Field(..., gt=0, description="Amount to pay in ZMW")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    phone_number: str = Field(..., description="Customer's phone number")


class PaymentConfirmRequest(BaseModel):
    """Request to confirm delivery and release funds."""
    transaction_id: UUID = Field(..., description="ID of the transaction")


class TransactionResponse(BaseModel):
    """Transaction response."""
    id: UUID
    bid_id: UUID
    buyer_id: UUID
    farmer_id: UUID
    amount: float
    platform_fee: float
    farmer_payout: float
    status: PaymentStatus
    payment_method: Optional[str] = None
    flutterwave_reference: Optional[str] = None
    initiated_at: datetime
    paid_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Payment initiation response."""
    message: str
    transaction_id: UUID
    status: PaymentStatus
    payment_url: Optional[str] = None
    flutterwave_reference: Optional[str] = None


class WebhookRequest(BaseModel):
    """Flutterwave webhook request."""
    event: str
    data: dict
    status: Optional[str] = None
    transaction_id: Optional[int] = None
    payment_id: Optional[str] = None


class PayoutRequest(BaseModel):
    """Request to release escrow to farmer."""
    transaction_id: UUID
