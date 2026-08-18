"""
================================================================================
LISTING API ENDPOINTS
================================================================================

This file defines all the API endpoints for listing operations.

Each endpoint:
1. Receives HTTP request
2. Validates input (using Pydantic schemas)
3. Calls CRUD functions
4. Returns HTTP response

Endpoint Summary:
    POST   /                  → Create a new listing
    GET    /                  → Search listings with filters
    GET    /{listing_id}      → Get a single listing
    PATCH  /{listing_id}      → Update a listing
    DELETE /{listing_id}      → Delete a listing
    POST   /{listing_id}/sold → Mark listing as sold

Why RESTful design?
1. Consistent URL structure
2. Uses HTTP methods appropriately (GET, POST, PATCH, DELETE)
3. Predictable for clients
4. Follows industry standards

================================================================================
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    ListingCreate,
    ListingUpdate,
    ListingResponse,
    ListingSearch,
    ListingListResponse,
    ListingStatus,
)
from app.crud import (
    create_listing,
    get_listing,
    get_listings,
    get_farmer_listings,
    update_listing,
    update_listing_status,
    delete_listing,
)
from app.spatial import extract_coordinates

# ============================================================================
# ROUTER
# ============================================================================
# Create a router for listing endpoints
# This router is included in main.py with prefix "/api/v1/listings"
router = APIRouter()


# ============================================================================
# CREATE LISTING
# ============================================================================
@router.post(
    "/",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listing",
    description="""
    Create a new produce listing.

    A farmer can list produce for sale.
    The listing includes:
    - What is being sold (produce_type, quantity, unit, price)
    - Where it is located (latitude, longitude, district, province)
    - Optional description and photos

    The listing is active for 14 days before expiring.

    Example Request:
        {
            "produce_type": "tomatoes",
            "quantity": 100,
            "unit": "kg",
            "price": 2500,
            "latitude": -15.3875,
            "longitude": 28.3228,
            "district": "Lusaka",
            "province": "Lusaka Province"
        }
    """
)
async def create_listing_endpoint(
    listing_data: ListingCreate,
    farmer_id: UUID = Query(..., description="ID of the farmer creating the listing"),
    db: AsyncSession = Depends(get_db),
) -> ListingResponse:
    """
    Create a new listing.

    Args:
        listing_data: Listing data from request body
        farmer_id: Farmer ID from query parameter
        db: Database session

    Returns:
        ListingResponse: The created listing

    Note:
        In a real implementation, farmer_id would come from JWT authentication.
        For now, it's passed as a query parameter for simplicity.
    """
    # Create the listing
    listing = await create_listing(db, listing_data, farmer_id)

    # Extract latitude and longitude from PostGIS POINT
    latitude, longitude = extract_coordinates(listing)

    # Convert to response schema
    return ListingResponse(
        id=listing.id,
        farmer_id=listing.farmer_id,
        produce_type=listing.produce_type,
        quantity=listing.quantity,
        unit=listing.unit,
        price=listing.price,
        latitude=latitude,
        longitude=longitude,
        district=listing.district,
        province=listing.province,
        status=listing.status,
        description=listing.description,
        photos=listing.photos or [],
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        expires_at=listing.expires_at,
        sold_at=listing.sold_at,
    )


# ============================================================================
# SEARCH LISTINGS
# ============================================================================
@router.get(
    "/",
    response_model=ListingListResponse,
    summary="Search listings",
    description="""
    Search for listings with filters and pagination.

    Supports:
    - Text search (produce_type, district, province)
    - Price range (min_price, max_price)
    - Spatial search (latitude, longitude, radius_km)
    - Pagination (page, per_page)

    If latitude and longitude are provided, results are sorted by distance.

    Example:
        GET /api/v1/listings?produce_type=tomatoes&district=Lusaka&page=1&per_page=20
    """
)
async def search_listings(
    produce_type: Optional[str] = Query(None, description="Filter by produce type"),
    district: Optional[str] = Query(None, description="Filter by district"),
    province: Optional[str] = Query(None, description="Filter by province"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    status: Optional[ListingStatus] = Query(
        ListingStatus.ACTIVE,
        description="Filter by status"
    ),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="User latitude for distance search"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="User longitude for distance search"),
    radius_km: Optional[float] = Query(None, ge=1, le=500, description="Search radius in kilometers"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> ListingListResponse:
    """
    Search listings with filters.

    This is the main search endpoint for buyers.
    It supports multiple filters and pagination.
    """
    # Get listings with filters
    listings, total = await get_listings(
        db=db,
        produce_type=produce_type,
        district=district,
        province=province,
        min_price=min_price,
        max_price=max_price,
        status=status,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        page=page,
        per_page=per_page,
    )

    # Convert to response schemas
    items = []
    for listing in listings:
        lat, lng = extract_coordinates(listing)
        items.append(
            ListingResponse(
                id=listing.id,
                farmer_id=listing.farmer_id,
                produce_type=listing.produce_type,
                quantity=listing.quantity,
                unit=listing.unit,
                price=listing.price,
                latitude=lat,
                longitude=lng,
                district=listing.district,
                province=listing.province,
                status=listing.status,
                description=listing.description,
                photos=listing.photos or [],
                created_at=listing.created_at,
                updated_at=listing.updated_at,
                expires_at=listing.expires_at,
                sold_at=listing.sold_at,
            )
        )

    # Calculate total pages
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return ListingListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ============================================================================
# GET SINGLE LISTING
# ============================================================================
@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Get a listing by ID",
    description="Get detailed information about a specific listing."
)
async def get_listing_endpoint(
    listing_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ListingResponse:
    """
    Get a single listing by ID.

    Args:
        listing_id: UUID of the listing
        db: Database session

    Returns:
        ListingResponse: The listing details

    Raises:
        HTTPException 404: If listing not found
    """
    # Get the listing
    listing = await get_listing(db, listing_id)

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found",
        )

    # Extract coordinates
    latitude, longitude = extract_coordinates(listing)

    # Return response
    return ListingResponse(
        id=listing.id,
        farmer_id=listing.farmer_id,
        produce_type=listing.produce_type,
        quantity=listing.quantity,
        unit=listing.unit,
        price=listing.price,
        latitude=latitude,
        longitude=longitude,
        district=listing.district,
        province=listing.province,
        status=listing.status,
        description=listing.description,
        photos=listing.photos or [],
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        expires_at=listing.expires_at,
        sold_at=listing.sold_at,
    )


# ============================================================================
# UPDATE LISTING
# ============================================================================
@router.patch(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Update a listing",
    description="Update one or more fields of a listing. Only the owner can update."
)
async def update_listing_endpoint(
    listing_id: UUID,
    listing_data: ListingUpdate,
    farmer_id: UUID = Query(..., description="ID of the farmer (for ownership check)"),
    db: AsyncSession = Depends(get_db),
) -> ListingResponse:
    """
    Update a listing.

    Args:
        listing_id: UUID of the listing
        listing_data: Updated data
        farmer_id: Farmer ID (for ownership check)
        db: Database session

    Returns:
        ListingResponse: The updated listing

    Raises:
        HTTPException 404: If listing not found
        HTTPException 403: If farmer doesn't own the listing
    """
    try:
        listing = await update_listing(db, listing_id, listing_data, farmer_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found",
        )

    # Extract coordinates
    latitude, longitude = extract_coordinates(listing)

    return ListingResponse(
        id=listing.id,
        farmer_id=listing.farmer_id,
        produce_type=listing.produce_type,
        quantity=listing.quantity,
        unit=listing.unit,
        price=listing.price,
        latitude=latitude,
        longitude=longitude,
        district=listing.district,
        province=listing.province,
        status=listing.status,
        description=listing.description,
        photos=listing.photos or [],
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        expires_at=listing.expires_at,
        sold_at=listing.sold_at,
    )


# ============================================================================
# MARK AS SOLD
# ============================================================================
@router.post(
    "/{listing_id}/sold",
    response_model=ListingResponse,
    summary="Mark a listing as sold",
    description="Mark a listing as sold. This sets status to 'sold' and records sold_at timestamp."
)
async def mark_listing_sold(
    listing_id: UUID,
    farmer_id: UUID = Query(..., description="ID of the farmer (for ownership check)"),
    db: AsyncSession = Depends(get_db),
) -> ListingResponse:
    """
    Mark a listing as sold.

    This is called when a farmer accepts a bid.
    The listing is no longer available for bidding.

    Args:
        listing_id: UUID of the listing
        farmer_id: Farmer ID (for ownership check)
        db: Database session

    Returns:
        ListingResponse: The updated listing
    """
    try:
        listing = await update_listing_status(
            db,
            listing_id,
            ListingStatus.SOLD,
            farmer_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found",
        )

    # Extract coordinates
    latitude, longitude = extract_coordinates(listing)

    return ListingResponse(
        id=listing.id,
        farmer_id=listing.farmer_id,
        produce_type=listing.produce_type,
        quantity=listing.quantity,
        unit=listing.unit,
        price=listing.price,
        latitude=latitude,
        longitude=longitude,
        district=listing.district,
        province=listing.province,
        status=listing.status,
        description=listing.description,
        photos=listing.photos or [],
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        expires_at=listing.expires_at,
        sold_at=listing.sold_at,
    )


# ============================================================================
# DELETE LISTING
# ============================================================================
@router.delete(
    "/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a listing",
    description="Delete a listing. Only the owner can delete, and sold listings cannot be deleted."
)
async def delete_listing_endpoint(
    listing_id: UUID,
    farmer_id: UUID = Query(..., description="ID of the farmer (for ownership check)"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a listing.

    Args:
        listing_id: UUID of the listing
        farmer_id: Farmer ID (for ownership check)
        db: Database session

    Raises:
        HTTPException 404: If listing not found
        HTTPException 403: If farmer doesn't own the listing
        HTTPException 400: If listing is sold (can't delete)
    """
    try:
        deleted = await delete_listing(db, listing_id, farmer_id)
    except ValueError as e:
        # Check if it's the "cannot delete sold" error
        if "Cannot delete a sold listing" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found",
        )

    # Return 204 No Content (no response body)
