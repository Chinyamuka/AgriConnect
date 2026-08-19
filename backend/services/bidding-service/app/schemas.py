"""
================================================================================
PYDANTIC SCHEMAS FOR BIDDING SERVICE
================================================================================

This file defines the data structures for API requests and responses.

Why Pydantic?
1. Automatic validation (ensures data is correct)
2. Type hints (IDE autocomplete)
3. Serialization (convert to/from JSON)
4. Documentation (auto-generated API docs)

================================================================================
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================
class BidStatus(str, Enum):
    """Status of a bid."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# ============================================================================
# SCHEMAS
# ============================================================================
class BidBase(BaseModel):
    """Base bid schema with common fields."""
    listing_id: UUID = Field(..., description="ID of the listing being bid on")
    amount: float = Field(..., gt=0, description="Bid amount in Zambian Kwacha")
    message: Optional[str] = Field(None, max_length=500, description="Optional message to farmer")


class BidCreate(BidBase):
    """Schema for placing a new bid."""
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Bid amount must be greater than 0')
        return v


class BidResponse(BidBase):
    """Schema for bid response."""
    id: UUID
    buyer_id: UUID
    farmer_id: UUID
    status: BidStatus
    created_at: datetime
    updated_at: datetime
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    transaction_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class BidListResponse(BaseModel):
    """Schema for paginated bid list response."""
    items: List[BidResponse]
    total: int
    page: int
    per_page: int
    pages: int


class BidAcceptRequest(BaseModel):
    """Schema for accepting a bid."""
    bid_id: UUID = Field(..., description="ID of the bid to accept")


class BidAcceptResponse(BaseModel):
    """Schema for bid acceptance response."""
    message: str
    bid_id: UUID
    transaction_id: UUID


# ============================================================================
# KAFKA EVENTS
# ============================================================================
class BidPlacedEvent(BaseModel):
    """Event published when a bid is placed."""
    event_type: str = "bid.placed"
    bid_id: UUID
    listing_id: UUID
    buyer_id: UUID
    farmer_id: UUID
    amount: float
    timestamp: datetime = Field(default_factory=datetime.now)


class BidAcceptedEvent(BaseModel):
    """Event published when a bid is accepted."""
    event_type: str = "bid.accepted"
    bid_id: UUID
    listing_id: UUID
    buyer_id: UUID
    farmer_id: UUID
    amount: float
    transaction_id: UUID
    timestamp: datetime = Field(default_factory=datetime.now)


class BidRejectedEvent(BaseModel):
    """Event published when a bid is rejected."""
    event_type: str = "bid.rejected"
    bid_id: UUID
    listing_id: UUID
    buyer_id: UUID
    farmer_id: UUID
    amount: float
    timestamp: datetime = Field(default_factory=datetime.now)
