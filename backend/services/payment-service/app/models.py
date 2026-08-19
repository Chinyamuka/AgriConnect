"""
================================================================================
SQLALCHEMY MODELS FOR PAYMENT SERVICE
================================================================================

This file defines the database schema for transactions and escrow.

Key Concepts:
1. Transaction - A payment transaction from buyer to farmer
2. Escrow - Funds held in trust until delivery is confirmed
3. Payment Log - Immutable audit trail for all payment actions

================================================================================
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.database import Base


class Transaction(Base):
    """
    Transaction model - Represents a payment transaction.
    
    Lifecycle:
    1. INITIATED → Payment started
    2. PENDING → Awaiting payment
    3. PROCESSING → Processing with Flutterwave
    4. PAID_ESCROW → Funds in escrow
    5. DELIVERED → Goods delivered
    6. COMPLETED → Funds released to farmer
    7. REFUNDED → Refunded to buyer
    8. FAILED → Payment failed
    """
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bid_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    buyer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    farmer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False, default=0.0)
    farmer_payout = Column(Float, nullable=False, default=0.0)
    
    status = Column(String(20), nullable=False, default="initiated", index=True)
    
    payment_method = Column(String(50), nullable=True)
    flutterwave_reference = Column(String(100), nullable=True, index=True)
    
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    
    # Renamed from 'metadata' to 'extra_data' to avoid SQLAlchemy conflict
    extra_data = Column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('idx_transactions_bid', 'bid_id'),
        Index('idx_transactions_status', 'status'),
        Index('idx_transactions_buyer_status', 'buyer_id', 'status'),
        Index('idx_transactions_farmer_status', 'farmer_id', 'status'),
    )


class PaymentLog(Base):
    """
    Immutable audit log for payment actions.
    
    This is CRITICAL for:
    1. Auditing - Every action is recorded
    2. Dispute resolution - Complete history
    3. Debugging - Track what happened when
    4. Compliance - Financial regulations
    
    NEVER DELETE OR MODIFY PAYMENT LOGS!
    """
    __tablename__ = "payment_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    transaction_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    action = Column(String(50), nullable=False)
    status_before = Column(String(20), nullable=True)
    status_after = Column(String(20), nullable=True)
    
    amount = Column(Float, nullable=True)
    flutterwave_reference = Column(String(100), nullable=True)
    
    # Renamed from 'metadata' to 'extra_data' to avoid SQLAlchemy conflict
    extra_data = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_payment_logs_transaction', 'transaction_id'),
        Index('idx_payment_logs_action', 'action'),
        Index('idx_payment_logs_created_at', 'created_at'),
    )
