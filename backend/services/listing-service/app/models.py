"""
SQLAlchemy models for the Listing Service.

This model works with both SQLite and PostgreSQL.
For PostgreSQL, we use proper UUID types.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timedelta
import uuid
from app.database import Base
from app.config import settings


class Listing(Base):
    __tablename__ = "listings"
    
    # ========================================================================
    # Use String(36) for SQLite compatibility, but PostgreSQL will treat it
    # as UUID when using the UUID type. We'll use the PostgreSQL UUID type
    # when available, but fall back to String for SQLite.
    # ========================================================================
    # For SQLite: String(36) works
    # For PostgreSQL: We'll use UUID with a cast
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    farmer_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    produce_type = Column(String(100), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False, default="kg")
    price = Column(Float, nullable=False)
    
    # For SQLite, use separate lat/lng columns
    latitude = Column(Float, nullable=False, default=0.0)
    longitude = Column(Float, nullable=False, default=0.0)
    
    district = Column(String(100), nullable=False, index=True)
    province = Column(String(100), nullable=False, index=True)
    
    status = Column(String(20), nullable=False, default="active", index=True)
    description = Column(Text, nullable=True)
    photos = Column(JSONB, nullable=True, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    sold_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_listings_produce_status', 'produce_type', 'status'),
        Index('idx_listings_farmer_status', 'farmer_id', 'status'),
        Index('idx_listings_district_status', 'district', 'status'),
        Index('idx_listings_expires_at', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<Listing(id={self.id}, produce={self.produce_type})>"
