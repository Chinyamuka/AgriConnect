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
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from app.models import Listing
from app.schemas import ListingCreate, ListingUpdate, ListingStatus
from app.config import settings
from app.spatial import get_listings_in_radius, get_listings_by_district, extract_coordinates


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

    This is called when a farmer creates a new produce listing.
    
    For SQLite compatibility, we store latitude and longitude as separate fields.
    In production with PostgreSQL, these would be stored as a PostGIS POINT.

    Args:
        db: Database session
        listing_data: Listing data from API request
        farmer_id: ID of the farmer creating the listing

    Returns:
        Listing: The created listing object
    """
    # For SQLite, we store latitude and longitude as separate fields
    # In production with PostgreSQL, we would use a PostGIS POINT
    listing = Listing(
        farmer_id=farmer_id,
        produce_type=listing_data.produce_type,
        quantity=listing_data.quantity,
        unit=listing_data.unit,
        price=listing_data.price,
        latitude=listing_data.latitude,   # ← Use latitude directly
        longitude=listing_data.longitude,  # ← Use longitude directly
        district=listing_data.district,
        province=listing_data.province,
        description=listing_data.description,
        photos=listing_data.photos,
        status=ListingStatus.ACTIVE,
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

    This is the main search function for the API.
    Supports:
    - Text filters (produce_type, district, province)
    - Numeric filters (min_price, max_price)
    - Spatial search (latitude, longitude, radius_km)
    - Pagination (page, per_page)

    Args:
        db: Database session
        produce_type: Filter by produce type (partial match)
        district: Filter by district (partial match)
        province: Filter by province (partial match)
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
    """
    # Get the listing
    listing = await get_listing(db, listing_id)

    if not listing:
        return None

    # Check ownership
    if listing.farmer_id != farmer_id:
        raise ValueError("You do not own this listing")

    # Update fields if provided
    update_data = listing_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(listing, field, value)

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
