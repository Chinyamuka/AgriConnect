"""
================================================================================
POSTGIS SPATIAL UTILITIES FOR LISTING SERVICE
================================================================================

This file provides spatial query functions using PostgreSQL/PostGIS.

Why PostGIS?
1. Native spatial operations in SQL
2. GiST indexes for fast spatial searches
3. ST_DWithin for radius queries
4. ST_Distance for distance calculations
5. SRID 4326 for GPS coordinates

Key Functions:
1. get_listings_in_radius - Find listings within a distance
2. get_listings_by_district - Find listings in a district
3. get_listings_by_province - Find listings in a province
4. distance_km - Calculate distance between two points (pure Python fallback)

================================================================================
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from geoalchemy2 import functions
from typing import Optional, List
from app.models import Listing
import math


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
    Find listings within a specified radius using PostGIS ST_DWithin.
    
    This is the most important spatial function.
    It allows buyers to find produce near their location.
    
    How it works:
    1. Convert user's lat/lng to a PostGIS POINT
    2. Use ST_DWithin to find listings within radius
    3. ST_DWithin uses the GiST index for fast searches
    4. Results are ordered by distance (closest first)
    
    Args:
        db: Database session
        latitude: User's latitude (-90 to 90)
        longitude: User's longitude (-180 to 180)
        radius_km: Search radius in kilometers
        produce_type: Optional filter by produce type
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        limit: Maximum number of results
        offset: Pagination offset
    
    Returns:
        List[Listing]: Listings within radius, sorted by distance
    
    SQL Equivalent:
        SELECT * FROM listings
        WHERE ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326),
            radius_km * 1000
        )
        AND status = 'active'
        ORDER BY ST_Distance(location, ST_SetSRID(ST_MakePoint(longitude, latitude), 4326))
        LIMIT 20 OFFSET 0;
    
    Why ST_DWithin?
    - Uses GiST index (fast even with millions of rows)
    - Returns true if geometries are within distance
    - Distance is in meters (so we multiply radius_km by 1000)
    """
    # Create the user's location as a PostGIS point
    # ST_SetSRID: Sets the coordinate system (4326 = WGS 84)
    # ST_MakePoint: Creates a point from longitude, latitude
    user_location = func.ST_SetSRID(
        func.ST_MakePoint(longitude, latitude),
        4326
    )
    
    # Build the query
    query = (
        db.query(Listing)
        .filter(Listing.status == "active")  # Only active listings
        .filter(
            # ST_DWithin: Returns true if geometries are within distance
            # Distance is in meters, so multiply radius_km by 1000
            func.ST_DWithin(
                Listing.location,      # The listing's location (PostGIS POINT)
                user_location,         # The user's location (PostGIS POINT)
                radius_km * 1000       # Distance in meters
            )
        )
    )
    
    # Apply optional filters
    if produce_type:
        query = query.filter(Listing.produce_type.ilike(f"%{produce_type}%"))
    
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    
    # Order by distance (closest first)
    # ST_Distance: Calculates distance between two geometries
    query = query.order_by(
        func.ST_Distance(Listing.location, user_location)
    )
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute the query
    result = await db.execute(query)
    listings = result.scalars().all()
    
    return listings


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
    
    This is a simpler search that doesn't require GPS coordinates.
    Useful when users know which district they're in.
    
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
    
    # Order by newest first
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
    
    Similar to district search but at the province level.
    Useful for broader searches.
    
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
# HAVERSINE DISTANCE (Fallback)
# ============================================================================
def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate distance between two points using the Haversine formula.
    
    This is a pure Python implementation that doesn't require PostGIS.
    Used as a fallback or for testing.
    
    The Haversine formula calculates the great-circle distance
    between two points on a sphere (Earth).
    
    Formula:
        a = sin²(Δφ/2) + cos(φ1) * cos(φ2) * sin²(Δλ/2)
        c = 2 * atan2(√a, √(1-a))
        d = R * c
        
    Where:
        φ is latitude, λ is longitude
        R is Earth's radius (6371 km)
    
    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)
    
    Returns:
        float: Distance in kilometers
    
    Example:
        >>> haversine_distance(-15.3875, 28.3228, -12.9686, 28.6324)
        269.5  # Lusaka to Ndola is about 270 km
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
# UTILITY: Extract Latitude and Longitude
# ============================================================================
def extract_coordinates(listing: Listing) -> tuple[float, float]:
    """
    Extract latitude and longitude from a PostGIS POINT.
    
    PostGIS POINT stores coordinates as (longitude, latitude).
    This function extracts them as (latitude, longitude) for API responses.
    
    Args:
        listing: Listing model with location field
    
    Returns:
        tuple[float, float]: (latitude, longitude)
    
    Note:
        In PostGIS, POINT(x, y) where x = longitude, y = latitude
        So we return (y, x) to match the standard (lat, lng) order
    """
    if listing.location is None:
        return (0.0, 0.0)
    
    # location is a PostGIS POINT with x=longitude, y=latitude
    longitude = listing.location.x
    latitude = listing.location.y
    
    return (latitude, longitude)
