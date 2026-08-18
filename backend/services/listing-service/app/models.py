"""
================================================================================
SQLALCHEMY MODELS FOR LISTING SERVICE
================================================================================

This file defines the database schema using SQLAlchemy ORM.

Why SQLAlchemy Models?
1. Python classes that map to database tables
2. Automatic SQL generation (no raw SQL)
3. Type safety (columns have Python types)
4. Relationships (foreign keys, joins)
5. Migration generation (with Alembic)

Why PostGIS Geometry?
1. Location is stored as a PostGIS POINT
2. Enables spatial queries (ST_DWithin, ST_Distance)
3. Uses GiST indexes for fast searches
4. Standard SRID 4326 (GPS coordinates)

================================================================================
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import uuid
from app.database import Base
from app.config import settings


class Listing(Base):
    """
    Listing model - Represents a produce listing.
    
    A listing is created by a farmer and contains:
    - What is being sold (produce_type, quantity, unit, price)
    - Where it is located (location, district, province)
    - Status (active, sold, expired, pending_review, flagged)
    - Metadata (description, photos, timestamps)
    
    Table: listings
    """
    __tablename__ = "listings"
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    # Why UUID instead of Integer?
    # 1. Cannot be guessed (security - users can't enumerate IDs)
    # 2. Distributed generation (services can create IDs independently)
    # 3. No collisions (UUID v4 is practically unique)
    # 4. API safe (exposing UUIDs in URLs is safe)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the listing (UUID v4)"
    )
    
    # ========================================================================
    # FOREIGN KEY REFERENCE
    # ========================================================================
    # farmer_id: References the User Service
    # 
    # Why store only the ID and not the full user data?
    # 1. Database-per-service pattern - User data is in User Service DB
    # 2. Decoupling - Listing Service doesn't depend on User Service schema
    # 3. If we need user data, we call the User Service API
    # 4. Data consistency - User Service is the source of truth for users
    farmer_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="ID of the farmer who created this listing (from User Service)"
    )
    
    # ========================================================================
    # LISTING DETAILS
    # ========================================================================
    produce_type = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Type of produce (e.g., tomatoes, maize, onions, groundnuts)"
    )
    
    quantity = Column(
        Float,
        nullable=False,
        doc="Quantity of produce (e.g., 100)"
    )
    
    unit = Column(
        String(20),
        nullable=False,
        default="kg",
        doc="Unit of measurement (kg, ton, bundle, bag)"
    )
    
    price = Column(
        Float,
        nullable=False,
        doc="Asking price in Zambian Kwacha (K)"
    )
    
    # ========================================================================
    # LOCATION - PostGIS Geometry
    # ========================================================================
    # Why PostGIS Geometry?
    # 1. Spatial queries: ST_DWithin, ST_Distance, ST_Contains
    # 2. GiST indexes: Fast spatial searches
    # 3. SRID 4326: Standard GPS coordinate system
    # 4. Native PostgreSQL support
    #
    # The location is stored as a POINT (longitude, latitude)
    # Example: POINT(28.3228 -15.3875) for Lusaka
    location = Column(
        Geometry(geometry_type='POINT', srid=4326),
        nullable=False,
        index=True,
        doc="GPS coordinates as PostGIS POINT (longitude, latitude)"
    )
    
    district = Column(
        String(100),
        nullable=False,
        index=True,
        doc="District where the produce is located (e.g., Mkushi, Lusaka)"
    )
    
    province = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Province where the produce is located"
    )
    
    # ========================================================================
    # STATUS
    # ========================================================================
    # Status lifecycle:
    #   1. active     → Listing is available for bidding
    #   2. pending_review → Awaiting admin review (fraud check)
    #   3. sold       → Listing has been sold
    #   4. expired    → 14 days passed without being sold
    #   5. flagged    → Marked for fraud/abuse
    status = Column(
        String(20),
        nullable=False,
        default="active",
        index=True,
        doc="Status: active, sold, expired, pending_review, flagged"
    )
    
    # ========================================================================
    # ADDITIONAL DATA
    # ========================================================================
    description = Column(
        Text,
        nullable=True,
        doc="Optional description of the produce (quality, variety, etc.)"
    )
    
    photos = Column(
        JSONB,
        nullable=True,
        default=list,
        doc="List of photo URLs (stored in S3/Cloudinary)"
    )
    
    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    # Why track timestamps?
    # 1. Audit trail - Know when things happened
    # 2. Ordering - Show newest listings first
    # 3. Analytics - Track listing activity
    # 4. Expiry - Know when to expire listings
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When the listing was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="When the listing was last updated"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When the listing expires (14 days after creation)"
    )
    
    sold_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the listing was sold (set when status becomes 'sold')"
    )
    
    # ========================================================================
    # OPTIMISTIC LOCKING
    # ========================================================================
    # Why version?
    # 1. Prevent concurrent updates from overwriting each other
    # 2. If two users try to update the same listing at the same time
    # 3. The first one succeeds, the second gets an error
    version = Column(
        Integer,
        default=1,
        nullable=False,
        doc="Optimistic locking version (increments on update)"
    )
    
    # ========================================================================
    # INDEXES
    # ========================================================================
    # Why indexes?
    # 1. Faster queries (no full table scan)
    # 2. GiST index on location for spatial queries
    # 3. Composite indexes for common filter combinations
    __table_args__ = (
        # GiST index on location for fast spatial queries
        # This is what makes "find listings within 50km" fast
        Index('idx_listings_location', location, postgresql_using='gist'),
        
        # Composite indexes for common filters
        # Query: WHERE produce_type = 'tomatoes' AND status = 'active'
        Index('idx_listings_produce_status', 'produce_type', 'status'),
        
        # Query: WHERE farmer_id = '...' AND status = 'active'
        Index('idx_listings_farmer_status', 'farmer_id', 'status'),
        
        # Query: WHERE district = 'Lusaka' AND status = 'active'
        Index('idx_listings_district_status', 'district', 'status'),
        
        # Query: WHERE expires_at < NOW() AND status = 'active'
        Index('idx_listings_expires_at', 'expires_at'),
    )
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<Listing(id={self.id}, produce={self.produce_type}, price={self.price})>"
