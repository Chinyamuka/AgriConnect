"""
================================================================================
FLUTTERWAVE API CLIENT
================================================================================

This module handles communication with the Flutterwave API.

Flutterwave supports:
1. Mobile Money charges (Airtel, MTN, Zamtel)
2. Card payments
3. Transfers (payouts to farmers)
4. Webhooks for payment confirmation

Why Flutterwave?
1. Supports Zambian mobile money (Airtel, MTN, Zamtel)
2. Escrow functionality
3. International card payments
4. Good documentation

================================================================================
"""
import httpx
import json
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from app.config import settings

logger = logging.getLogger(__name__)


class FlutterwaveClient:
    """
    HTTP client for Flutterwave API.
    
    Sandbox URL: https://api.flutterwave.com/v3
    Production URL: https://api.flutterwave.com/v3
    
    API Keys:
    - Public Key: Used for client-side operations
    - Secret Key: Used for server-side operations (keep secret!)
    - Encryption Key: Used for encrypting payloads
    """
    
    def __init__(self):
        """Initialize the Flutterwave client."""
        self.base_url = settings.flutterwave_base_url
        self.secret_key = settings.flutterwave_secret_key
        self.encryption_key = settings.flutterwave_encryption_key
        self.timeout = 30.0
        
        # Headers required for all Flutterwave API calls
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
    
    # ========================================================================
    # MOBILE MONEY CHARGE
    # ========================================================================
    async def charge_mobile_money(
        self,
        amount: float,
        phone_number: str,
        currency: str = "ZMW",
        payment_method: str = "mobile_money_zambia",
        network: str = "MTN",  # MTN, Airtel, Zamtel
        tx_ref: str = None,
        redirect_url: str = None,
    ) -> Dict[str, Any]:
        """
        Charge a customer using mobile money.
        
        Supported networks in Zambia:
        - MTN MoMo
        - Airtel Money
        - Zamtel Kwacha
        
        Args:
            amount: Amount in ZMW
            phone_number: Customer's phone number
            currency: Currency code (ZMW)
            payment_method: 'mobile_money_zambia'
            network: 'MTN', 'Airtel', 'Zamtel'
            tx_ref: Unique transaction reference
            redirect_url: Redirect URL after payment
        
        Returns:
            Dict: Flutterwave response
        
        API Endpoint:
            POST /v3/charges?type=mobile_money_zambia
        
        Example Response:
            {
                "status": "success",
                "message": "Charge initiated",
                "data": {
                    "id": 12345,
                    "tx_ref": "...",
                    "flw_ref": "...",
                    "amount": 2500,
                    "status": "pending"
                }
            }
        """
        # Generate a transaction reference if not provided
        if not tx_ref:
            import uuid
            tx_ref = f"tx_{uuid.uuid4().hex[:12]}"
        
        # Build the payload for mobile money charge
        payload = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": currency,
            "phone_number": phone_number,
            "network": network,
            "payment_method": payment_method,
            "fullname": "AgriConnect User",
            "email": "user@agriconnect.com",
            "redirect_url": redirect_url or "https://agriconnect.com/payment/complete",
            "meta": {
                "source": "AgriConnect",
                "type": "farm_produce_purchase",
            }
        }
        
        # Flutterwave charges endpoint with type parameter
        url = f"{self.base_url}/charges?type={payment_method}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ Mobile money charge initiated: {tx_ref}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Flutterwave API error: {e.response.text}")
            raise Exception(f"Payment initiation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ Flutterwave connection error: {str(e)}")
            raise
    
    # ========================================================================
    # CARD PAYMENT
    # ========================================================================
    async def charge_card(
        self,
        amount: float,
        card_number: str,
        cvv: str,
        expiry_month: str,
        expiry_year: str,
        phone_number: str,
        currency: str = "ZMW",
        tx_ref: str = None,
    ) -> Dict[str, Any]:
        """
        Charge a customer using a card.
        
        Args:
            amount: Amount in ZMW
            card_number: Card number
            cvv: CVV code
            expiry_month: Expiry month (MM)
            expiry_year: Expiry year (YYYY)
            phone_number: Customer's phone number
            currency: Currency code
            tx_ref: Unique transaction reference
        
        Returns:
            Dict: Flutterwave response
        """
        if not tx_ref:
            import uuid
            tx_ref = f"tx_{uuid.uuid4().hex[:12]}"
        
        payload = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": currency,
            "card_number": card_number,
            "cvv": cvv,
            "expiry_month": expiry_month,
            "expiry_year": expiry_year,
            "phone_number": phone_number,
            "email": "user@agriconnect.com",
            "fullname": "AgriConnect User",
            "meta": {
                "source": "AgriConnect",
                "type": "farm_produce_purchase",
            }
        }
        
        url = f"{self.base_url}/charges?type=card"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ Card charge initiated: {tx_ref}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Card charge failed: {str(e)}")
            raise
    
    # ========================================================================
    # TRANSFER (Payout to Farmer)
    # ========================================================================
    async def transfer_funds(
        self,
        amount: float,
        account_bank: str,
        account_number: str,
        beneficiary_name: str,
        currency: str = "ZMW",
        reference: str = None,
        narration: str = "Payment for farm produce",
    ) -> Dict[str, Any]:
        """
        Transfer funds to a farmer's bank account or mobile money.
        
        This is used to release escrow funds to the farmer.
        
        Args:
            amount: Amount to transfer
            account_bank: Bank code or 'MOMO' for mobile money
            account_number: Account number or phone number
            beneficiary_name: Recipient's full name
            currency: Currency code
            reference: Unique reference
            narration: Description of the transfer
        
        Returns:
            Dict: Flutterwave response
        
        API Endpoint:
            POST /v3/transfers
        """
        if not reference:
            import uuid
            reference = f"ref_{uuid.uuid4().hex[:12]}"
        
        payload = {
            "amount": amount,
            "currency": currency,
            "account_bank": account_bank,
            "account_number": account_number,
            "beneficiary_name": beneficiary_name,
            "reference": reference,
            "narration": narration,
            "callback_url": f"{settings.flutterwave_base_url}/webhooks/transfer",
            "meta": {
                "source": "AgriConnect",
                "type": "farmer_payout",
            }
        }
        
        url = f"{self.base_url}/transfers"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ Transfer initiated: {reference}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Transfer failed: {str(e)}")
            raise
    
    # ========================================================================
    # VERIFY TRANSACTION
    # ========================================================================
    async def verify_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """
        Verify a transaction status with Flutterwave.
        
        Args:
            transaction_id: Flutterwave transaction ID
        
        Returns:
            Dict: Transaction details
        
        API Endpoint:
            GET /v3/transactions/{id}/verify
        """
        url = f"{self.base_url}/transactions/{transaction_id}/verify"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self.headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ Transaction verified: {transaction_id}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Transaction verification failed: {str(e)}")
            raise


# Create a singleton instance
flutterwave_client = FlutterwaveClient()
