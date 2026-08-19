"""
================================================================================
SQLALCHEMY MODELS FOR BIDDING SERVICE
================================================================================

This file defines the database schema for bids.

Key Concepts:
1. A bid is an offer from a buyer to a farmer
2. Bids have a status: pending, accepted, rejected, withdrawn
3. When a bid is accepted, a transaction is created
4. Redis locks prevent double-selling

================================================================================
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base


class Bid(Base):
    """
    Bid model - Represents an offer from a buyer to a farmer.
    
    Lifecycle:
    1. PENDING → Buyer places bid, waiting for farmer response
    2. ACCEPTED → Farmer accepts bid → Transaction created
    3. REJECTED → Farmer rejects bid → Buyer notified
    4. WITHDRAWN → Buyer withdraws bid before farmer responds
    """
    __tablename__ = "bids"
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # ========================================================================
    # RELATIONSHIPS (References to other services)
    # ========================================================================
    listing_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="ID of the listing being bid on (from Listing Service)"
    )
    
    buyer_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="ID of the buyer placing the bid (from User Service)"
    )
    
    farmer_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="ID of the farmer who owns the listing (from User Service)"
    )
    
    # ========================================================================
    # BID DETAILS
    # ========================================================================
    amount = Column(
        Float,
        nullable=False,
        doc="Bid amount in Zambian Kwacha (K)"
    )
    
    # ========================================================================
    # STATUS
    # ========================================================================
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        doc="Status: pending, accepted, rejected, withdrawn"
    )
    
    # ========================================================================
    # OPTIONAL FIELDS
    # ========================================================================
    message = Column(
        Text,
        nullable=True,
        doc="Optional message from buyer to farmer"
    )
    
    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    accepted_at = Column(
        DateTime,
        nullable=True,
        doc="When the bid was accepted (if accepted)"
    )
    
    rejected_at = Column(
        DateTime,
        nullable=True,
        doc="When the bid was rejected (if rejected)"
    )
    
    # ========================================================================
    # TRANSACTION REFERENCE
    # ========================================================================
    transaction_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="ID of the transaction created when bid is accepted (from Payment Service)"
    )
    
    # ========================================================================
    # VERSION - Optimistic Locking
    # ========================================================================
    version = Column(
        Integer,
        default=1,
        nullable=False,
        doc="Optimistic locking version"
    )
    
    # ========================================================================
    # INDEXES
    # ========================================================================
    __table_args__ = (
        Index('idx_bids_listing_status', 'listing_id', 'status'),
        Index('idx_bids_buyer_status', 'buyer_id', 'status'),
        Index('idx_bids_farmer_status', 'farmer_id', 'status'),
        Index('idx_bids_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Bid(id={self.id}, listing={self.listing_id}, amount={self.amount}, status={self.status})>"
