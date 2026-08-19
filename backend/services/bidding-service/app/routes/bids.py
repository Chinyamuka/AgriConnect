"""
================================================================================
BID API ENDPOINTS
================================================================================

This file defines all the API endpoints for bid operations.

Endpoint Summary:
    POST   /                → Place a bid
    GET    /listing/{id}    → Get bids for a listing
    GET    /buyer/{id}      → Get bids by a buyer
    GET    /farmer/{id}     → Get bids received by a farmer
    POST   /{id}/accept     → Accept a bid (with Redis lock)
    POST   /{id}/reject     → Reject a bid
    GET    /{id}            → Get a single bid

================================================================================
"""
import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid as uuid_lib

from app.database import get_db
from app.schemas import (
    BidCreate,
    BidResponse,
    BidListResponse,
    BidStatus,
    BidAcceptResponse,
)
from app.crud import (
    create_bid,
    get_bid,
    get_listing_bids,
    get_buyer_bids,
    get_farmer_bids,
    accept_bid,
    reject_bid,
)
from app.redis_client import redis_client
from app.kafka_producer import kafka_producer
from app.listing_client import listing_client
from app.config import settings

# ============================================================================
# LOGGER
# ============================================================================
logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# PLACE A BID
# ============================================================================
@router.post(
    "/",
    response_model=BidResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a bid",
    description="Place a bid on an active listing."
)
async def place_bid(
    bid_data: BidCreate,
    buyer_id: UUID = Query(..., description="ID of the buyer placing the bid"),
    db: AsyncSession = Depends(get_db),
) -> BidResponse:
    """
    Place a bid on a listing.
    
    Process:
        1. Validate listing exists and is active
        2. Get farmer_id from listing
        3. Create bid in database
        4. Publish bid.placed event
    """
    # Step 1: Validate listing exists
    listing = await listing_client.get_listing(bid_data.listing_id)
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {bid_data.listing_id} not found"
        )
    
    # Step 2: Check listing is active
    if listing.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Listing is {listing.get('status')}. Only active listings can receive bids."
        )
    
    # Step 3: Get farmer_id from listing
    farmer_id = listing.get("farmer_id")
    if not farmer_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Listing has no farmer_id"
        )
    
    # Step 4: Convert farmer_id to UUID
    try:
        farmer_uuid = UUID(farmer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid farmer_id format"
        )
    
    # Step 5: Create bid
    bid = await create_bid(db, bid_data, buyer_id, farmer_uuid)
    
    # Step 6: Publish event
    await kafka_producer.publish_bid_placed(bid)
    
    # Step 7: Return response
    return BidResponse(
        id=bid.id,
        listing_id=bid.listing_id,
        buyer_id=bid.buyer_id,
        farmer_id=bid.farmer_id,
        amount=bid.amount,
        message=bid.message,
        status=bid.status,
        created_at=bid.created_at,
        updated_at=bid.updated_at,
        accepted_at=bid.accepted_at,
        rejected_at=bid.rejected_at,
        transaction_id=bid.transaction_id,
    )


# ============================================================================
# GET BIDS FOR A LISTING
# ============================================================================
@router.get(
    "/listing/{listing_id}",
    response_model=BidListResponse,
    summary="Get bids for a listing",
    description="Get all bids placed on a specific listing."
)
async def get_listing_bids_endpoint(
    listing_id: UUID,
    status_filter: Optional[BidStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BidListResponse:
    """
    Get all bids for a listing.
    
    Used by farmers to see who has bid on their produce.
    """
    bids, total = await get_listing_bids(
        db, listing_id, status_filter, page, per_page
    )
    
    items = [
        BidResponse(
            id=bid.id,
            listing_id=bid.listing_id,
            buyer_id=bid.buyer_id,
            farmer_id=bid.farmer_id,
            amount=bid.amount,
            message=bid.message,
            status=bid.status,
            created_at=bid.created_at,
            updated_at=bid.updated_at,
            accepted_at=bid.accepted_at,
            rejected_at=bid.rejected_at,
            transaction_id=bid.transaction_id,
        )
        for bid in bids
    ]
    
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return BidListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ============================================================================
# GET BIDS BY BUYER
# ============================================================================
@router.get(
    "/buyer/{buyer_id}",
    response_model=BidListResponse,
    summary="Get bids by buyer",
    description="Get all bids placed by a specific buyer."
)
async def get_buyer_bids_endpoint(
    buyer_id: UUID,
    status_filter: Optional[BidStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BidListResponse:
    """Get all bids placed by a buyer."""
    bids, total = await get_buyer_bids(db, buyer_id, status_filter, page, per_page)
    
    items = [
        BidResponse(
            id=bid.id,
            listing_id=bid.listing_id,
            buyer_id=bid.buyer_id,
            farmer_id=bid.farmer_id,
            amount=bid.amount,
            message=bid.message,
            status=bid.status,
            created_at=bid.created_at,
            updated_at=bid.updated_at,
            accepted_at=bid.accepted_at,
            rejected_at=bid.rejected_at,
            transaction_id=bid.transaction_id,
        )
        for bid in bids
    ]
    
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return BidListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ============================================================================
# GET BIDS RECEIVED BY FARMER
# ============================================================================
@router.get(
    "/farmer/{farmer_id}",
    response_model=BidListResponse,
    summary="Get bids received by farmer",
    description="Get all bids received by a specific farmer."
)
async def get_farmer_bids_endpoint(
    farmer_id: UUID,
    status_filter: Optional[BidStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BidListResponse:
    """Get all bids received by a farmer."""
    bids, total = await get_farmer_bids(db, farmer_id, status_filter, page, per_page)
    
    items = [
        BidResponse(
            id=bid.id,
            listing_id=bid.listing_id,
            buyer_id=bid.buyer_id,
            farmer_id=bid.farmer_id,
            amount=bid.amount,
            message=bid.message,
            status=bid.status,
            created_at=bid.created_at,
            updated_at=bid.updated_at,
            accepted_at=bid.accepted_at,
            rejected_at=bid.rejected_at,
            transaction_id=bid.transaction_id,
        )
        for bid in bids
    ]
    
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return BidListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ============================================================================
# GET A SINGLE BID
# ============================================================================
@router.get(
    "/{bid_id}",
    response_model=BidResponse,
    summary="Get a single bid",
    description="Get a specific bid by ID."
)
async def get_bid_endpoint(
    bid_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BidResponse:
    """Get a single bid by ID."""
    bid = await get_bid(db, bid_id)
    
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid {bid_id} not found"
        )
    
    return BidResponse(
        id=bid.id,
        listing_id=bid.listing_id,
        buyer_id=bid.buyer_id,
        farmer_id=bid.farmer_id,
        amount=bid.amount,
        message=bid.message,
        status=bid.status,
        created_at=bid.created_at,
        updated_at=bid.updated_at,
        accepted_at=bid.accepted_at,
        rejected_at=bid.rejected_at,
        transaction_id=bid.transaction_id,
    )


# ============================================================================
# ACCEPT A BID (With Redis Lock)
# ============================================================================
@router.post(
    "/{bid_id}/accept",
    response_model=BidAcceptResponse,
    summary="Accept a bid",
    description="""
    Accept a bid on a listing.
    
    This uses a Redis distributed lock to prevent double-selling.
    Only one bid can be accepted at a time per listing.
    
    When a bid is accepted:
    1. Redis lock is acquired on the listing
    2. Database row-level lock is used
    3. The bid status is updated to 'accepted'
    4. The listing is marked as 'sold'
    5. A transaction is created (placeholder)
    6. Events are published
    """
)
async def accept_bid_endpoint(
    bid_id: UUID,
    farmer_id: UUID = Query(..., description="ID of the farmer accepting the bid"),
    db: AsyncSession = Depends(get_db),
) -> BidAcceptResponse:
    """
    Accept a bid with Redis distributed lock.
    
    This is the most critical operation in the system.
    It prevents double-selling a listing.
    """
    # Step 1: Get the bid
    bid = await get_bid(db, bid_id)
    
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid {bid_id} not found"
        )
    
    # Step 2: Verify the farmer owns the listing
    if bid.farmer_id != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this listing"
        )
    
    # Step 3: Check bid status
    if bid.status != BidStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid is already {bid.status}. Only pending bids can be accepted."
        )
    
    # Step 4: Check if the listing is still active
    listing = await listing_client.get_listing(bid.listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {bid.listing_id} not found"
        )
    
    if listing.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This listing is no longer active"
        )
    
    # ========================================================================
    # Step 5: Acquire Redis distributed lock
    # ========================================================================
    lock_key = f"lock:listing:{bid.listing_id}"
    lock_acquired = await redis_client.acquire_lock(
        lock_key,
        timeout=settings.lock_timeout_seconds
    )
    
    if not lock_acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This listing is currently being processed. Please try again in a few seconds."
        )
    
    try:
        # ====================================================================
        # Step 6: Database transaction with row-level lock
        # ====================================================================
        accepted_bid = await accept_bid(db, bid_id)
        
        if not accepted_bid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to accept bid"
            )
        
        # ====================================================================
        # Step 7: Update listing status to 'sold'
        # ====================================================================
        listing_updated = await listing_client.update_listing_status(
            listing_id=bid.listing_id,
            status="sold",
            farmer_id=farmer_id,
        )
        
        if not listing_updated:
            # Rollback the bid acceptance if listing update fails
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update listing status"
            )
        
        # ====================================================================
        # Step 8: Create a transaction ID (placeholder for Payment Service)
        # ====================================================================
        transaction_id = uuid_lib.uuid4()
        
        # ====================================================================
        # Step 9: Publish Kafka events
        # ====================================================================
        await kafka_producer.publish_bid_accepted(accepted_bid, transaction_id)
        
        # ====================================================================
        # Step 10: Return response
        # ====================================================================
        return BidAcceptResponse(
            message="Bid accepted successfully! Transaction created.",
            bid_id=accepted_bid.id,
            transaction_id=transaction_id,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error accepting bid: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept bid: {str(e)}"
        )
    finally:
        # ====================================================================
        # Step 11: Release Redis lock
        # ====================================================================
        await redis_client.release_lock(lock_key)
        logger.info(f"🔓 Lock released: {lock_key}")


# ============================================================================
# REJECT A BID
# ============================================================================
@router.post(
    "/{bid_id}/reject",
    response_model=dict,
    summary="Reject a bid",
    description="Reject a pending bid."
)
async def reject_bid_endpoint(
    bid_id: UUID,
    farmer_id: UUID = Query(..., description="ID of the farmer rejecting the bid"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reject a bid.
    
    The farmer can reject a bid if they don't agree with the amount.
    """
    # Step 1: Get the bid
    bid = await get_bid(db, bid_id)
    
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid {bid_id} not found"
        )
    
    # Step 2: Verify the farmer owns the listing
    if bid.farmer_id != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this listing"
        )
    
    # Step 3: Check bid status
    if bid.status != BidStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid is already {bid.status}. Only pending bids can be rejected."
        )
    
    # Step 4: Reject the bid
    rejected_bid = await reject_bid(db, bid_id)
    
    if not rejected_bid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject bid"
        )
    
    # Step 5: Publish event
    await kafka_producer.publish_bid_rejected(rejected_bid)
    
    return {
        "message": "Bid rejected successfully",
        "bid_id": str(rejected_bid.id),
    }
