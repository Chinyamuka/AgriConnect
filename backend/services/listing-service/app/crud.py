"""
================================================================================
CRUD OPERATIONS FOR LISTING SERVICE
================================================================================

This file contains all Create, Read, Update, Delete operations for listings.

Why separate CRUD from routes?
1. Separation of concerns - routes handle HTTP, CRUD handles database
2. Reusability - CRUD functions can be used by multiple routes
3. Testability - CRUD functions can be tested independently
4. Cleaner code - Routes stay focused on HTTP logic

Each function follows this pattern:
1. Validate input (via Pydantic schemas)
2. Execute database operation
3. Return result or raise exception
4. Publish events (for changes)

================================================================================
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from app.models import Listing
from app.schemas import ListingCreate, ListingUpdate, ListingStatus
from app.config import settings
from app.spatial import get_listings_in_radius, get_listings_by_district


# ============================================================================
# CREATE
# ============================================================================
async def create_listing(
    db: AsyncSession,
    listing_data: ListingCreate,
    farmer_id: UUID,
) -> Listing:
    """
    Create a new listing in the database.
    
    Args:
        db: Database session
        listing_data: Listing data from API request
        farmer_id: ID of the farmer creating the listing
    
    Returns:
        Listing: The created listing object
    
    Process:
        1. Convert latitude/longitude to PostGIS POINT
        2. Set expiry date (14 days from now)
        3. Set initial status to 'active'
        4. Save to database
        5. Return the created listing
    
    Why:
        - Creates a new produce listing for a farmer
        - Location is stored as PostGIS POINT for spatial queries
        - Expiry is automatic (14 days)
        - Status starts as 'active'
    
    Example:
        Listing data: {produce_type: "tomatoes", quantity: 100, price: 2500, ...}
        Result: New listing stored in database with ID
    """
    # Create the PostGIS POINT from latitude/longitude
    # SRID 4326 = WGS 84 (standard GPS coordinate system)
    point_wkt = f"POINT({listing_data.longitude} {listing_data.latitude})"
    
    # Create the listing model instance
    listing = Listing(
        farmer_id=farmer_id,
        produce_type=listing_data.produce_type,
        quantity=listing_data.quantity,
        unit=listing_data.unit,
        price=listing_data.price,
        location=point_wkt,  # PostGIS POINT in WKT format
        district=listing_data.district,
        province=listing_data.province,
        description=listing_data.description,
        photos=listing_data.photos,
        status=ListingStatus.ACTIVE,  # New listings start as active
        expires_at=datetime.utcnow() + timedelta(days=settings.max_listing_age_days),
    )
    
    # Add to database and commit
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    
    return listing


# ============================================================================
# READ - Single Listing
# ============================================================================
async def get_listing(
    db: AsyncSession,
    listing_id: UUID,
) -> Optional[Listing]:
    """
    Get a single listing by ID.
    
    Args:
        db: Database session
        listing_id: UUID of the listing
    
    Returns:
        Listing: The listing object, or None if not found
    
    Why:
        - Retrieve a specific listing for viewing
        - Used for detail pages, bids, payments
        - Returns None if not found (404)
    """
    query = select(Listing).where(Listing.id == listing_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# ============================================================================
# READ - Listings with Filters
# ============================================================================
async def get_listings(
    db: AsyncSession,
    produce_type: Optional[str] = None,
    district: Optional[str] = None,
    province: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    status: Optional[ListingStatus] = ListingStatus.ACTIVE,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Listing], int]:
    """
    Get listings with filters and pagination.
    
    Args:
        db: Database session
        produce_type: Filter by produce type
        district: Filter by district
        province: Filter by province
        min_price: Minimum price filter
        max_price: Maximum price filter
        status: Filter by status (default: active)
        latitude: User's latitude for distance search
        longitude: User's longitude for distance search
        radius_km: Search radius in kilometers
        page: Page number for pagination
        per_page: Items per page
    
    Returns:
        Tuple[List[Listing], int]: (listings, total_count)
    
    Why:
        - Main search endpoint for buyers
        - Supports filtering by produce, location, price
        - Supports distance-based search (if lat/long provided)
        - Pagination for performance
    
    Process:
        1. If lat/long provided → Use spatial search (ST_DWithin)
        2. Otherwise → Use normal filter query
        3. Apply all filters
        4. Count total matching records
        5. Apply pagination
        6. Return results
    """
    # If location is provided, use spatial search
    if latitude is not None and longitude is not None and radius_km is not None:
        listings = await get_listings_in_radius(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            produce_type=produce_type,
            min_price=min_price,
            max_price=max_price,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        # Get total count (approximate for spatial search)
        total = len(listings)
        return listings, total
    
    # Otherwise, build normal filter query
    query = select(Listing)
    
    # Apply filters
    if produce_type:
        query = query.where(Listing.produce_type.ilike(f"%{produce_type}%"))
    
    if district:
        query = query.where(Listing.district.ilike(f"%{district}%"))
    
    if province:
        query = query.where(Listing.province.ilike(f"%{province}%"))
    
    if min_price is not None:
        query = query.where(Listing.price >= min_price)
    
    if max_price is not None:
        query = query.where(Listing.price <= max_price)
    
    if status:
        query = query.where(Listing.status == status)
    
    # Order by newest first
    query = query.order_by(Listing.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Execute
    result = await db.execute(query)
    listings = result.scalars().all()
    
    return listings, total


# ============================================================================
# READ - Farmer's Listings
# ============================================================================
async def get_farmer_listings(
    db: AsyncSession,
    farmer_id: UUID,
    status: Optional[ListingStatus] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Listing], int]:
    """
    Get all listings for a specific farmer.
    
    Args:
        db: Database session
        farmer_id: ID of the farmer
        status: Filter by status (optional)
        page: Page number
        per_page: Items per page
    
    Returns:
        Tuple[List[Listing], int]: (listings, total_count)
    
    Why:
        - Farmers need to see their own listings
        - Used for farmer dashboard
        - Can filter by status (active, sold, expired)
    """
    query = select(Listing).where(Listing.farmer_id == farmer_id)
    
    if status:
        query = query.where(Listing.status == status)
    
    query = query.order_by(Listing.created_at.desc())
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    listings = result.scalars().all()
    
    return listings, total


# ============================================================================
# UPDATE
# ============================================================================
async def update_listing(
    db: AsyncSession,
    listing_id: UUID,
    listing_data: ListingUpdate,
    farmer_id: UUID,
) -> Optional[Listing]:
    """
    Update a listing.
    
    Args:
        db: Database session
        listing_id: ID of the listing to update
        listing_data: Updated data
        farmer_id: ID of the farmer (for authorization)
    
    Returns:
        Listing: Updated listing, or None if not found
    
    Raises:
        ValueError: If farmer doesn't own the listing
    
    Why:
        - Farmers can update their listings
        - Only the owner can update
        - Partial updates supported (PATCH)
        - Updates updated_at timestamp automatically
    """
    # Get the listing
    listing = await get_listing(db, listing_id)
    
    if not listing:
        return None
    
    # Check ownership
    if listing.farmer_id != farmer_id:
        raise ValueError("You do not own this listing")
    
    # Update fields if provided
    update_data = listing_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(listing, field, value)
    
    # Update timestamp (SQLAlchemy auto-updates updated_at)
    await db.commit()
    await db.refresh(listing)
    
    return listing


# ============================================================================
# UPDATE - Status Only
# ============================================================================
async def update_listing_status(
    db: AsyncSession,
    listing_id: UUID,
    status: ListingStatus,
    farmer_id: Optional[UUID] = None,
) -> Optional[Listing]:
    """
    Update the status of a listing.
    
    Args:
        db: Database session
        listing_id: ID of the listing
        status: New status (active, sold, expired, etc.)
        farmer_id: Optional farmer ID for ownership check
    
    Returns:
        Listing: Updated listing, or None if not found
    
    Why:
        - Used when a listing is sold
        - Used when admin flags a listing
        - Used when a listing expires
        - Separate from full update for clarity
    """
    # Get the listing
    listing = await get_listing(db, listing_id)
    
    if not listing:
        return None
    
    # Check ownership if farmer_id provided
    if farmer_id and listing.farmer_id != farmer_id:
        raise ValueError("You do not own this listing")
    
    # Update status
    listing.status = status
    
    # If sold, record sold_at timestamp
    if status == ListingStatus.SOLD:
        listing.sold_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(listing)
    
    return listing


# ============================================================================
# DELETE
# ============================================================================
async def delete_listing(
    db: AsyncSession,
    listing_id: UUID,
    farmer_id: UUID,
) -> bool:
    """
    Delete a listing.
    
    Args:
        db: Database session
        listing_id: ID of the listing to delete
        farmer_id: ID of the farmer (for authorization)
    
    Returns:
        bool: True if deleted, False if not found
    
    Raises:
        ValueError: If farmer doesn't own the listing
    
    Why:
        - Farmers can delete their listings
        - Only if not sold (can't delete sold listing)
        - Hard delete (remove from database)
    """
    # Get the listing
    listing = await get_listing(db, listing_id)
    
    if not listing:
        return False
    
    # Check ownership
    if listing.farmer_id != farmer_id:
        raise ValueError("You do not own this listing")
    
    # Don't allow deleting sold listings
    if listing.status == ListingStatus.SOLD:
        raise ValueError("Cannot delete a sold listing")
    
    # Delete
    await db.delete(listing)
    await db.commit()
    
    return True


# ============================================================================
# EXPIRE OLD LISTINGS
# ============================================================================
async def expire_old_listings(
    db: AsyncSession,
) -> int:
    """
    Find and expire listings that are past their expiry date.
    
    Returns:
        int: Number of listings expired
    
    Why:
        - Listings automatically expire after 14 days
        - Run by Celery Beat daily
        - Clean up old listings
        - Keep search results fresh
    """
    now = datetime.utcnow()
    
    # Find all active listings that have expired
    query = (
        select(Listing)
        .where(Listing.status == ListingStatus.ACTIVE)
        .where(Listing.expires_at < now)
    )
    result = await db.execute(query)
    expired_listings = result.scalars().all()
    
    # Update their status
    for listing in expired_listings:
        listing.status = ListingStatus.EXPIRED
    
    # Commit all changes
    await db.commit()
    
    return len(expired_listings)
