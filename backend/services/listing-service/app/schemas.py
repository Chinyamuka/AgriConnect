"""
Pydantic schemas for the Listing Service.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class ListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    PENDING_REVIEW = "pending_review"
    FLAGGED = "flagged"


class ListingUnit(str, Enum):
    KG = "kg"
    TON = "ton"
    BUNDLE = "bundle"
    BAG = "bag"


class ListingBase(BaseModel):
    produce_type: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(..., gt=0)
    unit: ListingUnit = ListingUnit.KG
    price: float = Field(..., gt=0)
    district: str = Field(..., min_length=1, max_length=100)
    province: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    photos: List[str] = Field(default_factory=list)


class ListingCreate(ListingBase):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class ListingUpdate(BaseModel):
    produce_type: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[ListingUnit] = None
    price: Optional[float] = Field(None, gt=0)
    district: Optional[str] = Field(None, min_length=1, max_length=100)
    province: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    status: Optional[ListingStatus] = None


class ListingResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    produce_type: str
    quantity: float
    unit: str
    price: float
    latitude: float
    longitude: float
    district: str
    province: str
    status: ListingStatus
    description: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    sold_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ListingSearch(BaseModel):
    produce_type: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, ge=1, le=500)
    status: Optional[ListingStatus] = ListingStatus.ACTIVE
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class ListingListResponse(BaseModel):
    items: List[ListingResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# KAFKA EVENTS
# ============================================================================
class ListingCreatedEvent(BaseModel):
    event_type: str = "listing.created"
    listing_id: UUID
    farmer_id: UUID
    produce_type: str
    quantity: float
    unit: str
    price: float
    district: str
    province: str
    latitude: float
    longitude: float
    timestamp: datetime = Field(default_factory=datetime.now)


class ListingUpdatedEvent(BaseModel):
    event_type: str = "listing.updated"
    listing_id: UUID
    farmer_id: UUID
    changes: dict
    timestamp: datetime = Field(default_factory=datetime.now)


class ListingExpiredEvent(BaseModel):
    event_type: str = "listing.expired"
    listing_id: UUID
    farmer_id: UUID
    produce_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
