"""
================================================================================
CRUD OPERATIONS FOR PAYMENT SERVICE
================================================================================
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from app.models import Transaction, PaymentLog
from app.schemas import PaymentStatus


# ============================================================================
# TRANSACTION CRUD
# ============================================================================
async def create_transaction(
    db: AsyncSession,
    bid_id: UUID,
    buyer_id: UUID,
    farmer_id: UUID,
    amount: float,
    platform_fee: float,
    farmer_payout: float,
) -> Transaction:
    """Create a new transaction."""
    transaction = Transaction(
        bid_id=bid_id,
        buyer_id=buyer_id,
        farmer_id=farmer_id,
        amount=amount,
        platform_fee=platform_fee,
        farmer_payout=farmer_payout,
        status=PaymentStatus.INITIATED,
    )
    
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


async def get_transaction(
    db: AsyncSession,
    transaction_id: UUID,
) -> Optional[Transaction]:
    """Get a transaction by ID."""
    query = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_transaction_by_bid(
    db: AsyncSession,
    bid_id: UUID,
) -> Optional[Transaction]:
    """Get a transaction by bid ID."""
    query = select(Transaction).where(Transaction.bid_id == bid_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_transaction_status(
    db: AsyncSession,
    transaction_id: UUID,
    status: PaymentStatus,
    flutterwave_reference: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[Transaction]:
    """Update transaction status."""
    transaction = await get_transaction(db, transaction_id)
    
    if not transaction:
        return None
    
    # Create payment log before updating
    await create_payment_log(
        db=db,
        transaction_id=transaction_id,
        action=f"status_change_{status.value}",
        status_before=transaction.status.value,
        status_after=status.value,
        amount=transaction.amount,
        flutterwave_reference=flutterwave_reference,
        details=metadata,
    )
    
    # Update status
    transaction.status = status
    
    # Set timestamps based on status
    if status == PaymentStatus.PAID_ESCROW:
        transaction.paid_at = datetime.utcnow()
    elif status == PaymentStatus.DELIVERED:
        transaction.delivered_at = datetime.utcnow()
    elif status == PaymentStatus.COMPLETED:
        transaction.completed_at = datetime.utcnow()
    elif status == PaymentStatus.REFUNDED:
        transaction.refunded_at = datetime.utcnow()
    
    if flutterwave_reference:
        transaction.flutterwave_reference = flutterwave_reference
    
    if metadata:
        transaction.metadata = metadata
    
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


# ============================================================================
# PAYMENT LOG CRUD
# ============================================================================
async def create_payment_log(
    db: AsyncSession,
    transaction_id: UUID,
    action: str,
    status_before: Optional[str] = None,
    status_after: Optional[str] = None,
    amount: Optional[float] = None,
    flutterwave_reference: Optional[str] = None,
    details: Optional[dict] = None,
) -> PaymentLog:
    """Create an immutable payment log entry."""
    log = PaymentLog(
        transaction_id=transaction_id,
        action=action,
        status_before=status_before,
        status_after=status_after,
        amount=amount,
        flutterwave_reference=flutterwave_reference,
        details=details,
    )
    
    db.add(log)
    await db.commit()
    await db.refresh(log)
    
    return log


async def get_transaction_logs(
    db: AsyncSession,
    transaction_id: UUID,
) -> List[PaymentLog]:
    """Get all logs for a transaction."""
    query = select(PaymentLog).where(
        PaymentLog.transaction_id == transaction_id
    ).order_by(PaymentLog.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()
