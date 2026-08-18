"""
================================================================================
SPATIAL UTILITIES FOR LISTING SERVICE
================================================================================

This file provides spatial query functions using the Haversine formula.
Since we're using SQLite for development, we use a pure Python implementation
instead of PostGIS.

In production with PostgreSQL/PostGIS, we would use ST_DWithin and ST_Distance.

Why Haversine?
1. Calculates great-circle distance between two points on a sphere
2. Accurate enough for distances up to a few hundred kilometers
3. Pure Python implementation (works with SQLite)
4. No database dependency for distance calculations

================================================================================
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.models import Listing
import math


# ============================================================================
# HAVERSINE DISTANCE
# ============================================================================
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Uses the Haversine formula, which is accurate for small to medium distances.
    
    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)
    
    Returns:
        float: Distance in kilometers
    
    Formula:
        a = sin²(Δφ/2) + cos(φ1) * cos(φ2) * sin²(Δλ/2)
        c = 2 * atan2(√a, √(1-a))
        d = R * c
    
    Where:
        φ is latitude, λ is longitude
        R is Earth's radius (6371 km)
    """
    R = 6371  # Earth's radius in kilometers
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) *
        math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


# ============================================================================
# SPATIAL SEARCH - Find Listings Within Radius
# ============================================================================
async def get_listings_in_radius(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    radius_km: float,
    produce_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Listing]:
    """
    Find listings within a radius using the Haversine formula.
    
    Since we're using SQLite, we filter in Python after querying.
    In production with PostGIS, this would use ST_DWithin.
    
    Args:
        db: Database session
        latitude: User's latitude
        longitude: User's longitude
        radius_km: Search radius in kilometers
        produce_type: Optional filter by produce type
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        limit: Maximum number of results
        offset: Pagination offset
    
    Returns:
        List[Listing]: Listings within radius, sorted by distance
    """
    # Start with all active listings
    query = db.query(Listing).filter(Listing.status == "active")
    
    # Apply filters
    if produce_type:
        query = query.filter(Listing.produce_type.ilike(f"%{produce_type}%"))
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    
    # Execute query
    result = await db.execute(query)
    listings = result.scalars().all()
    
    # Filter by distance in Python (SQLite doesn't have ST_DWithin)
    filtered = []
    for listing in listings:
        # Calculate distance using Haversine formula
        dist = haversine_distance(
            latitude, longitude,
            listing.latitude, listing.longitude
        )
        if dist <= radius_km:
            filtered.append((listing, dist))
    
    # Sort by distance
    filtered.sort(key=lambda x: x[1])
    
    # Apply pagination
    filtered = filtered[offset:offset + limit]
    
    # Return only the listings
    return [item[0] for item in filtered]


# ============================================================================
# DISTRICT SEARCH
# ============================================================================
async def get_listings_by_district(
    db: AsyncSession,
    district: str,
    produce_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Listing]:
    """
    Get listings in a specific district.
    
    Args:
        db: Database session
        district: District name (case-insensitive)
        produce_type: Optional produce type filter
        limit: Maximum number of results
        offset: Pagination offset
    
    Returns:
        List[Listing]: Listings in the district, newest first
    """
    query = (
        db.query(Listing)
        .filter(Listing.status == "active")
        .filter(Listing.district.ilike(f"%{district}%"))
    )
    
    if produce_type:
        query = query.filter(Listing.produce_type.ilike(f"%{produce_type}%"))
    
    query = query.order_by(Listing.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# ============================================================================
# PROVINCE SEARCH
# ============================================================================
async def get_listings_by_province(
    db: AsyncSession,
    province: str,
    produce_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Listing]:
    """
    Get listings in a specific province.
    
    Args:
        db: Database session
        province: Province name (case-insensitive)
        produce_type: Optional produce type filter
        limit: Maximum number of results
        offset: Pagination offset
    
    Returns:
        List[Listing]: Listings in the province, newest first
    """
    query = (
        db.query(Listing)
        .filter(Listing.status == "active")
        .filter(Listing.province.ilike(f"%{province}%"))
    )
    
    if produce_type:
        query = query.filter(Listing.produce_type.ilike(f"%{produce_type}%"))
    
    query = query.order_by(Listing.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# ============================================================================
# EXTRACT COORDINATES
# ============================================================================
def extract_coordinates(listing) -> tuple[float, float]:
    """
    Extract latitude and longitude from a Listing object.
    
    In SQLite mode, we use the latitude and longitude fields directly.
    In PostgreSQL with PostGIS, we would extract from a PostGIS POINT.
    
    Args:
        listing: Listing model instance
    
    Returns:
        tuple[float, float]: (latitude, longitude)
    """
    return (listing.latitude, listing.longitude)
