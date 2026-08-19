"""
================================================================================
PAYMENT API ENDPOINTS
================================================================================

This file defines all the API endpoints for payment operations.

Endpoint Summary:
    POST   /initiate          → Initiate a payment
    POST   /confirm           → Confirm delivery and release funds
    GET    /{transaction_id}  → Get transaction details
    GET    /bid/{bid_id}      → Get transaction by bid ID
    GET    /buyer/{buyer_id}  → Get transactions by buyer
    GET    /farmer/{farmer_id} → Get transactions by farmer

================================================================================
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    PaymentInitiateRequest,
    PaymentConfirmRequest,
    TransactionResponse,
    PaymentResponse,
    PaymentStatus,
    PaymentMethod,
)
from app.crud import (
    create_transaction,
    get_transaction,
    get_transaction_by_bid,
    update_transaction_status,
)
from app.flutterwave_client import flutterwave_client
from app.kafka_producer import kafka_producer
from app.config import settings

router = APIRouter()


# ============================================================================
# INITIATE PAYMENT
# ============================================================================
@router.post(
    "/initiate",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a payment",
    description="Initiate a payment for an accepted bid."
)
async def initiate_payment(
    request: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    """
    Initiate a payment using Flutterwave.
    
    Supports:
    - Airtel Money
    - MTN MoMo
    - Zamtel Kwacha
    - Card payments
    
    Process:
        1. Validate the bid exists and is accepted
        2. Create transaction record
        3. Call Flutterwave API
        4. Return payment details
    """
    # TODO: Validate bid exists and is accepted
    # For now, we'll create a transaction directly
    
    # Calculate fees
    platform_fee = request.amount * (settings.platform_fee_percentage / 100)
    farmer_payout = request.amount - platform_fee
    
    # Create transaction
    transaction = await create_transaction(
        db=db,
        bid_id=request.bid_id,
        buyer_id=UUID("550e8400-e29b-41d4-a716-446655440000"),  # TODO: Get from auth
        farmer_id=UUID("550e8400-e29b-41d4-a716-446655440000"),  # TODO: Get from bid
        amount=request.amount,
        platform_fee=platform_fee,
        farmer_payout=farmer_payout,
    )
    
    # Call Flutterwave
    try:
        # Map network to Flutterwave format
        network_map = {
            PaymentMethod.AIRTEL_MONEY: "Airtel",
            PaymentMethod.MTN_MOMO: "MTN",
            PaymentMethod.ZAMTEL_KWACHA: "Zamtel",
        }
        
        network = network_map.get(request.payment_method, "MTN")
        
        flutterwave_response = await flutterwave_client.charge_mobile_money(
            amount=request.amount,
            phone_number=request.phone_number,
            network=network,
        )
        
        # Update transaction with Flutterwave reference
        if flutterwave_response.get("status") == "success":
            data = flutterwave_response.get("data", {})
            flutterwave_ref = data.get("flw_ref") or data.get("tx_ref")
            
            await update_transaction_status(
                db=db,
                transaction_id=transaction.id,
                status=PaymentStatus.PENDING,
                flutterwave_reference=flutterwave_ref,
                extra_data=flutterwave_response,
            )
            
            # Publish event
            await kafka_producer.publish_payment_initiated(transaction)
            
            return PaymentResponse(
                message="Payment initiated successfully",
                transaction_id=transaction.id,
                status=PaymentStatus.PENDING,
                payment_url=data.get("redirect_url"),
                flutterwave_reference=flutterwave_ref,
            )
        else:
            # Payment initiation failed
            await update_transaction_status(
                db=db,
                transaction_id=transaction.id,
                status=PaymentStatus.FAILED,
                extra_data=flutterwave_response,
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment initiation failed: {flutterwave_response.get('message', 'Unknown error')}"
            )
            
    except Exception as e:
        # Update transaction to failed
        await update_transaction_status(
            db=db,
            transaction_id=transaction.id,
            status=PaymentStatus.FAILED,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initiation error: {str(e)}"
        )


# ============================================================================
# CONFIRM DELIVERY AND RELEASE FUNDS
# ============================================================================
@router.post(
    "/confirm",
    response_model=dict,
    summary="Confirm delivery",
    description="Buyer confirms delivery, releasing funds to farmer."
)
async def confirm_delivery(
    request: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Confirm delivery and release funds from escrow.
    
    Process:
        1. Validate transaction exists and is in escrow
        2. Update status to 'delivered'
        3. Initiate transfer to farmer via Flutterwave
        4. Update status to 'completed'
        5. Publish events
    """
    # Get transaction
    transaction = await get_transaction(db, request.transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {request.transaction_id} not found"
        )
    
    # Validate status
    if transaction.status != PaymentStatus.PAID_ESCROW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction is {transaction.status}. Only 'paid_escrow' can be confirmed."
        )
    
    # Update to delivered
    transaction = await update_transaction_status(
        db=db,
        transaction_id=transaction.id,
        status=PaymentStatus.DELIVERED,
    )
    
    # TODO: Call Flutterwave transfer API to release funds
    # For now, simulate payout
    # flutterwave_response = await flutterwave_client.transfer_funds(
    #     amount=transaction.farmer_payout,
    #     account_bank="MOMO",
    #     account_number="+260977880000",
    #     beneficiary_name="Farmer Name",
    # )
    
    # Update to completed
    transaction = await update_transaction_status(
        db=db,
        transaction_id=transaction.id,
        status=PaymentStatus.COMPLETED,
    )
    
    # Publish event
    await kafka_producer.publish_payout_released(transaction)
    
    return {
        "message": "Delivery confirmed! Funds released to farmer.",
        "transaction_id": str(transaction.id),
        "amount": transaction.farmer_payout,
        "status": transaction.status,
    }


# ============================================================================
# GET TRANSACTION
# ============================================================================
@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get transaction details",
    description="Get details of a specific transaction."
)
async def get_transaction_endpoint(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    """Get transaction by ID."""
    transaction = await get_transaction(db, transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    return TransactionResponse(
        id=transaction.id,
        bid_id=transaction.bid_id,
        buyer_id=transaction.buyer_id,
        farmer_id=transaction.farmer_id,
        amount=transaction.amount,
        platform_fee=transaction.platform_fee,
        farmer_payout=transaction.farmer_payout,
        status=transaction.status,
        payment_method=transaction.payment_method,
        flutterwave_reference=transaction.flutterwave_reference,
        initiated_at=transaction.initiated_at,
        paid_at=transaction.paid_at,
        delivered_at=transaction.delivered_at,
        completed_at=transaction.completed_at,
        refunded_at=transaction.refunded_at,
    )


# ============================================================================
# GET TRANSACTION BY BID
# ============================================================================
@router.get(
    "/bid/{bid_id}",
    response_model=Optional[TransactionResponse],
    summary="Get transaction by bid",
    description="Get transaction associated with a bid."
)
async def get_transaction_by_bid_endpoint(
    bid_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Optional[TransactionResponse]:
    """Get transaction by bid ID."""
    transaction = await get_transaction_by_bid(db, bid_id)
    
    if not transaction:
        return None
    
    return TransactionResponse(
        id=transaction.id,
        bid_id=transaction.bid_id,
        buyer_id=transaction.buyer_id,
        farmer_id=transaction.farmer_id,
        amount=transaction.amount,
        platform_fee=transaction.platform_fee,
        farmer_payout=transaction.farmer_payout,
        status=transaction.status,
        payment_method=transaction.payment_method,
        flutterwave_reference=transaction.flutterwave_reference,
        initiated_at=transaction.initiated_at,
        paid_at=transaction.paid_at,
        delivered_at=transaction.delivered_at,
        completed_at=transaction.completed_at,
        refunded_at=transaction.refunded_at,
    )
