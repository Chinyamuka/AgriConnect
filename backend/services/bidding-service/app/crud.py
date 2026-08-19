"""
================================================================================
CRUD OPERATIONS FOR BIDDING SERVICE
================================================================================

This file contains all Create, Read, Update operations for bids.

Key Operations:
1. create_bid - Place a new bid
2. get_bid - Get a single bid
3. get_listing_bids - Get all bids for a listing
4. get_buyer_bids - Get all bids by a buyer
5. accept_bid - Accept a bid (with locking)
6. reject_bid - Reject a bid

================================================================================
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from app.models import Bid
from app.schemas import BidCreate, BidStatus


# ============================================================================
# CREATE
# ============================================================================
async def create_bid(
    db: AsyncSession,
    bid_data: BidCreate,
    buyer_id: UUID,
    farmer_id: UUID,
) -> Bid:
    """
    Place a new bid on a listing.
    
    Args:
        db: Database session
        bid_data: Bid data from API
        buyer_id: ID of the buyer placing the bid
        farmer_id: ID of the farmer (from listing)
    
    Returns:
        Bid: The created bid object
    
    Process:
        1. Validate listing exists and is active (called by API)
        2. Create bid with status 'pending'
        3. Save to database
    """
    bid = Bid(
        listing_id=bid_data.listing_id,
        buyer_id=buyer_id,
        farmer_id=farmer_id,
        amount=bid_data.amount,
        message=bid_data.message,
        status=BidStatus.PENDING,
    )
    
    db.add(bid)
    await db.commit()
    await db.refresh(bid)
    
    return bid


# ============================================================================
# READ
# ============================================================================
async def get_bid(
    db: AsyncSession,
    bid_id: UUID,
) -> Optional[Bid]:
    """
    Get a single bid by ID.
    
    Args:
        db: Database session
        bid_id: UUID of the bid
    
    Returns:
        Bid: The bid object, or None if not found
    """
    query = select(Bid).where(Bid.id == bid_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_listing_bids(
    db: AsyncSession,
    listing_id: UUID,
    status: Optional[BidStatus] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Bid], int]:
    """
    Get all bids for a listing.
    
    Args:
        db: Database session
        listing_id: ID of the listing
        status: Filter by status (optional)
        page: Page number
        per_page: Items per page
    
    Returns:
        Tuple[List[Bid], int]: (bids, total_count)
    """
    query = select(Bid).where(Bid.listing_id == listing_id)
    
    if status:
        query = query.where(Bid.status == status)
    
    # Order by newest first (descending)
    query = query.order_by(Bid.created_at.desc())
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    bids = result.scalars().all()
    
    return bids, total


async def get_buyer_bids(
    db: AsyncSession,
    buyer_id: UUID,
    status: Optional[BidStatus] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Bid], int]:
    """
    Get all bids placed by a buyer.
    
    Args:
        db: Database session
        buyer_id: ID of the buyer
        status: Filter by status (optional)
        page: Page number
        per_page: Items per page
    
    Returns:
        Tuple[List[Bid], int]: (bids, total_count)
    """
    query = select(Bid).where(Bid.buyer_id == buyer_id)
    
    if status:
        query = query.where(Bid.status == status)
    
    query = query.order_by(Bid.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    bids = result.scalars().all()
    
    return bids, total


async def get_farmer_bids(
    db: AsyncSession,
    farmer_id: UUID,
    status: Optional[BidStatus] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Bid], int]:
    """
    Get all bids received by a farmer.
    
    Args:
        db: Database session
        farmer_id: ID of the farmer
        status: Filter by status (optional)
        page: Page number
        per_page: Items per page
    
    Returns:
        Tuple[List[Bid], int]: (bids, total_count)
    """
    query = select(Bid).where(Bid.farmer_id == farmer_id)
    
    if status:
        query = query.where(Bid.status == status)
    
    query = query.order_by(Bid.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    bids = result.scalars().all()
    
    return bids, total


# ============================================================================
# UPDATE
# ============================================================================
async def accept_bid(
    db: AsyncSession,
    bid_id: UUID,
) -> Optional[Bid]:
    """
    Accept a bid.
    
    This is the most critical operation in the bidding service.
    It uses:
    1. Database row-level lock (SELECT FOR UPDATE)
    2. Status validation (only pending bids can be accepted)
    3. Timestamp recording
    
    Args:
        db: Database session
        bid_id: ID of the bid to accept
    
    Returns:
        Bid: The accepted bid, or None if not found
    
    Raises:
        ValueError: If bid is not in pending status
    """
    # Get the bid with row-level lock
    # SELECT FOR UPDATE locks the row until transaction is complete
    query = select(Bid).where(Bid.id == bid_id).with_for_update()
    result = await db.execute(query)
    bid = result.scalar_one_or_none()
    
    if not bid:
        return None
    
    # Validate status
    if bid.status != BidStatus.PENDING:
        raise ValueError(f"Bid is already {bid.status}. Only pending bids can be accepted.")
    
    # Update bid
    bid.status = BidStatus.ACCEPTED
    bid.accepted_at = datetime.utcnow()
    bid.version += 1
    
    await db.commit()
    await db.refresh(bid)
    
    return bid


async def reject_bid(
    db: AsyncSession,
    bid_id: UUID,
) -> Optional[Bid]:
    """
    Reject a bid.
    
    Args:
        db: Database session
        bid_id: ID of the bid to reject
    
    Returns:
        Bid: The rejected bid, or None if not found
    
    Raises:
        ValueError: If bid is not in pending status
    """
    bid = await get_bid(db, bid_id)
    
    if not bid:
        return None
    
    if bid.status != BidStatus.PENDING:
        raise ValueError(f"Bid is already {bid.status}. Only pending bids can be rejected.")
    
    bid.status = BidStatus.REJECTED
    bid.rejected_at = datetime.utcnow()
    bid.version += 1
    
    await db.commit()
    await db.refresh(bid)
    
    return bid


async def update_bid_transaction(
    db: AsyncSession,
    bid_id: UUID,
    transaction_id: UUID,
) -> Optional[Bid]:
    """
    Update a bid with the transaction ID after payment.
    
    Args:
        db: Database session
        bid_id: ID of the bid
        transaction_id: ID of the created transaction
    
    Returns:
        Bid: The updated bid, or None if not found
    """
    bid = await get_bid(db, bid_id)
    
    if not bid:
        return None
    
    bid.transaction_id = transaction_id
    
    await db.commit()
    await db.refresh(bid)
    
    return bid
