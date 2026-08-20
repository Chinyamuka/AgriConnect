"""
Main FastAPI application for the Messaging Gateway Service.
"""
import logging
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import SMSWebhookRequest, ParsedCommand, Command, Language
from app.commands import command_parser
from app.templates import SMSTemplates
from app.redis_client import redis_client
from app.kafka_producer import kafka_producer

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting Messaging Gateway Service...")
    await redis_client.connect()
    logger.info("✅ Connected to Redis")
    await kafka_producer.connect()
    logger.info("✅ Connected to Kafka")
    yield
    logger.info("🛑 Shutting down...")
    await redis_client.disconnect()
    await kafka_producer.disconnect()
    logger.info("✅ Shutdown complete")


# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(
    title="AgriConnect Messaging Gateway",
    description="SMS/USSD gateway for AgriConnect",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK
# ============================================================================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}


# ============================================================================
# SMS WEBHOOK
# ============================================================================
@app.post("/webhooks/sms")
async def sms_webhook(request: Request):
    """Handle SMS webhook from Africa's Talking."""
    try:
        data = await request.json()
        logger.info(f"📩 SMS webhook received: {data}")
        
        sms_request = SMSWebhookRequest(**data)
        logger.info(f"📩 SMS from {sms_request.phone}: {sms_request.text}")
        
        # Parse the command
        parsed = command_parser.parse(sms_request.text, sms_request.phone)
        
        if not parsed:
            response = SMSTemplates.get("help", Language.ENGLISH)
            return PlainTextResponse(response)
        
        # Process the command
        result = await process_command(parsed)
        
        # Publish to Kafka
        await kafka_producer.publish_sms_received(
            phone=sms_request.phone,
            text=sms_request.text,
            command=parsed.command.value,
            args=parsed.args,
            language=parsed.language.value,
            session_id=sms_request.session_id,
        )
        
        return PlainTextResponse(result)
        
    except Exception as e:
        logger.error(f"❌ Error processing SMS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMMAND PROCESSOR - Connects to Real APIs
# ============================================================================
async def process_command(parsed: ParsedCommand) -> str:
    """
    Process a parsed command and call the appropriate service APIs.
    """
    command = parsed.command
    
    # ========================================================================
    # HELP COMMAND
    # ========================================================================
    if command == Command.HELP:
        return SMSTemplates.get("help", parsed.language)
    
    # ========================================================================
    # SELL COMMAND - Create a Real Listing
    # ========================================================================
    elif command == Command.SELL:
        try:
            produce = parsed.args[0] if len(parsed.args) > 0 else ""
            quantity = float(parsed.args[1]) if len(parsed.args) > 1 else 0
            unit = parsed.args[2] if len(parsed.args) > 2 else "kg"
            price = float(parsed.args[3]) if len(parsed.args) > 3 else 0
            district = parsed.args[4] if len(parsed.args) > 4 else ""
            
            lat, lng = command_parser.get_location(district)
            farmer_id = "550e8400-e29b-41d4-a716-446655440000"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://localhost:8002/api/v1/listings/",
                    params={"farmer_id": farmer_id},
                    json={
                        "produce_type": produce,
                        "quantity": quantity,
                        "unit": unit,
                        "price": price,
                        "latitude": lat,
                        "longitude": lng,
                        "district": district,
                        "province": "Zambia",
                    }
                )
                
                if response.status_code == 201:
                    listing = response.json()
                    listing_id = listing.get("id")
                    return SMSTemplates.get(
                        "sell_success",
                        parsed.language,
                        listing_id=listing_id[:8],
                        produce=produce,
                        quantity=quantity,
                        unit=unit,
                        price=price,
                        district=district,
                    )
                else:
                    return f"❌ Failed to create listing."
                    
        except Exception as e:
            logger.error(f"❌ SELL command failed: {str(e)}")
            return "❌ Failed to create listing. Please try again."
    
    # ========================================================================
    # LIST COMMAND - Search Real Listings
    # ========================================================================
    elif command == Command.LIST:
        try:
            produce = parsed.args[0] if len(parsed.args) > 0 else ""
            district = parsed.args[1] if len(parsed.args) > 1 else ""
            
            params = {"status": "active"}
            if produce:
                params["produce_type"] = produce
            if district:
                params["district"] = district
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "http://localhost:8002/api/v1/listings/",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    listings = data.get("items", [])
                    
                    if not listings:
                        return "📋 No listings found."
                    
                    result = "📋 Listings found:\n"
                    for i, listing in enumerate(listings[:5]):
                        result += f"{i+1}. {listing['produce_type']} - {listing['quantity']}{listing['unit']} - K{listing['price']} - {listing['district']}\n"
                        result += f"   ID: {listing['id']}\n"
                    
                    if len(listings) > 5:
                        result += f"... and {len(listings) - 5} more"
                    
                    return result
                else:
                    return "❌ Failed to search listings."
                    
        except Exception as e:
            logger.error(f"❌ LIST command failed: {str(e)}")
            return "❌ Failed to search listings."
    
    # ========================================================================
    # BID COMMAND - Place a Real Bid
    # ========================================================================
    elif command == Command.BID:
        try:
            listing_id = parsed.args[0] if len(parsed.args) > 0 else ""
            amount = float(parsed.args[1]) if len(parsed.args) > 1 else 0
            
            if not listing_id:
                return "❌ Please provide a listing ID. Example: BID f3136a03-... 3000"
            
            buyer_id = "550e8400-e29b-41d4-a716-446655440000"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://localhost:8003/api/v1/bids/",
                    params={"buyer_id": buyer_id},
                    json={
                        "listing_id": listing_id,
                        "amount": amount,
                        "message": f"Bid via SMS from {parsed.phone}"
                    }
                )
                
                if response.status_code == 201:
                    bid = response.json()
                    bid_id = bid.get("id")
                    return f"✅ Bid placed! ID: {bid_id[:8]} for K{amount}"
                else:
                    return f"❌ Failed to place bid."
                    
        except Exception as e:
            logger.error(f"❌ BID command failed: {str(e)}")
            return "❌ Failed to place bid."
    
    # ========================================================================
    # ACCEPT COMMAND - Accept a Bid
    # ========================================================================
    elif command == Command.ACCEPT:
        try:
            bid_id = parsed.args[0] if len(parsed.args) > 0 else ""
            
            if not bid_id:
                return "❌ Please provide a bid ID. Example: ACCEPT 8d19daed-..."
            
            farmer_id = "550e8400-e29b-41d4-a716-446655440000"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"http://localhost:8003/api/v1/bids/{bid_id}/accept",
                    params={"farmer_id": farmer_id},
                )
                
                if response.status_code == 200:
                    result = response.json()
                    transaction_id = result.get("transaction_id", "")
                    return f"✅ Bid accepted! Transaction ID: {transaction_id[:8]}"
                elif response.status_code == 400:
                    return f"❌ {response.json().get('detail', 'Bid cannot be accepted')}"
                else:
                    return f"❌ Failed to accept bid."
                    
        except Exception as e:
            logger.error(f"❌ ACCEPT command failed: {str(e)}")
            return "❌ Failed to accept bid."
    
    # ========================================================================
    # PAY COMMAND - Initiate Payment
    # ========================================================================
    elif command == Command.PAY:
        try:
            transaction_id = parsed.args[0] if len(parsed.args) > 0 else ""
            amount = float(parsed.args[1]) if len(parsed.args) > 1 else 0
            
            if not transaction_id:
                return "❌ Please provide a transaction ID. Example: PAY b4a8ed94-..."
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                trans_response = await client.get(
                    f"http://localhost:8004/api/v1/payments/{transaction_id}"
                )
                
                if trans_response.status_code != 200:
                    return "❌ Transaction not found."
                
                transaction = trans_response.json()
                bid_id = transaction.get("bid_id")
                if not bid_id:
                    return "❌ Transaction has no associated bid."
                
                payment_response = await client.post(
                    "http://localhost:8004/api/v1/payments/initiate",
                    json={
                        "bid_id": bid_id,
                        "amount": amount if amount > 0 else transaction.get("amount", 0),
                        "payment_method": "airtel_money",
                        "phone_number": parsed.phone
                    }
                )
                
                if payment_response.status_code == 201:
                    result = payment_response.json()
                    flutterwave_ref = result.get("flutterwave_reference", "")
                    return f"💰 Payment initiated! Reference: {flutterwave_ref[:8] or transaction_id[:8]}"
                else:
                    return f"❌ Failed to initiate payment."
                    
        except Exception as e:
            logger.error(f"❌ PAY command failed: {str(e)}")
            return "❌ Failed to initiate payment."
    
    # ========================================================================
    # PRICE COMMAND - Get Market Price
    # ========================================================================
    elif command == Command.PRICE:
        produce = parsed.args[0] if len(parsed.args) > 0 else ""
        district = parsed.args[1] if len(parsed.args) > 1 else ""
        return f"📊 Average price for {produce} in {district or 'Zambia'}: K2500/kg"
    
    # ========================================================================
    # CONFIRM COMMAND - Confirm Delivery
    # ========================================================================
    elif command == Command.CONFIRM:
        transaction_id = parsed.args[0] if len(parsed.args) > 0 else ""
        if not transaction_id:
            return "❌ Please provide a transaction ID. Example: CONFIRM b4a8ed94-..."
        # TODO: Call Payment Service confirm endpoint
        return f"✅ Delivery confirmed for transaction {transaction_id[:8]}"
    
    # ========================================================================
    # RATE COMMAND - Rate a User
    # ========================================================================
    elif command == Command.RATE:
        user_id = parsed.args[0] if len(parsed.args) > 0 else ""
        score = parsed.args[1] if len(parsed.args) > 1 else ""
        return f"⭐ Rating submitted for user {user_id[:8] if user_id else 'unknown'}!"
    
    # ========================================================================
    # STATUS COMMAND - Check Order Status
    # ========================================================================
    elif command == Command.STATUS:
        order_id = parsed.args[0] if len(parsed.args) > 0 else ""
        if not order_id:
            return "❌ Please provide an order ID. Example: STATUS b4a8ed94-..."
        return f"📋 Order {order_id[:8]}: Processing"
    
    # ========================================================================
    # DEFAULT
    # ========================================================================
    return "⚠️ Command not implemented. Reply HELP for commands."


# ============================================================================
# USSD WEBHOOK
# ============================================================================
@app.post("/webhooks/ussd")
async def ussd_webhook(request: Request):
    """Handle USSD webhook from Africa's Talking."""
    try:
        data = await request.form()
        logger.info(f"📩 USSD webhook received: {data}")
        return PlainTextResponse("USSD coming soon!")
        
    except Exception as e:
        logger.error(f"❌ Error processing USSD: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
