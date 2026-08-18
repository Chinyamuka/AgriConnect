"""
Main FastAPI application for the Messaging Gateway Service.

Handles:
1. SMS webhooks from Africa's Talking
2. USSD webhooks from Africa's Talking
3. Command parsing and routing
4. Session management with Redis
5. Event publishing to Kafka
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    SMSWebhookRequest,
    USSDWebhookRequest,
    ParsedCommand,
    SMSResponse,
    USSDResponse,
    SMSReceivedEvent,
    USSDUpdatedEvent,
    Command,
    USSDState,
)
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
    """
    Startup and shutdown events.
    
    - Connect to Redis on startup
    - Connect to Kafka on startup
    - Disconnect on shutdown
    """
    # Startup
    logger.info("🚀 Starting Messaging Gateway Service...")
    await redis_client.connect()
    logger.info("✅ Connected to Redis")
    await kafka_producer.connect()
    logger.info("✅ Connected to Kafka")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Messaging Gateway Service...")
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


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================
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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.service_name,
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    # Check Redis connection
    try:
        await redis_client.get("health_check")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {str(e)}")
    
    return {"status": "ready"}


# ============================================================================
# SMS WEBHOOK
# ============================================================================
@app.post("/webhooks/sms")
async def sms_webhook(request: Request):
    """
    Handle SMS webhook from Africa's Talking.
    
    This endpoint receives SMS messages sent to AgriConnect.
    """
    try:
        # Parse request
        data = await request.json()
        logger.info(f"📩 SMS webhook received: {data}")
        
        # Validate request
        sms_request = SMSWebhookRequest(**data)
        logger.info(f"📩 SMS from {sms_request.phone}: {sms_request.text}")
        
        # Parse the command
        parsed = command_parser.parse(sms_request.text, sms_request.phone)
        
        if not parsed:
            # Invalid command
            response = SMSTemplates.get("help", Language.ENGLISH)
            return PlainTextResponse(response)
        
        # Process the command
        result = await process_command(parsed)
        
        # Publish to Kafka (for other services)
        event = SMSReceivedEvent(
            phone=sms_request.phone,
            text=sms_request.text,
            command=parsed.command.value,
            args=parsed.args,
            language=parsed.language.value,
            session_id=sms_request.session_id,
        )
        await kafka_producer.publish_sms_received(event)
        
        # Return response (will be sent as SMS)
        return PlainTextResponse(result)
        
    except Exception as e:
        logger.error(f"❌ Error processing SMS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# USSD WEBHOOK
# ============================================================================
@app.post("/webhooks/ussd")
async def ussd_webhook(request: Request):
    """
    Handle USSD webhook from Africa's Talking.
    
    This endpoint receives USSD session requests.
    """
    try:
        # Parse request
        data = await request.form()
        logger.info(f"📩 USSD webhook received: {data}")
        
        # Validate request
        ussd_request = USSDWebhookRequest(
            phone=data.get('phoneNumber'),
            session_id=data.get('sessionId'),
            session_state=data.get('sessionState'),
            text=data.get('text', ''),
            network=data.get('networkCode'),
        )
        
        logger.info(f"📩 USSD from {ussd_request.phone}: {ussd_request.text}")
        
        # Get or create USSD session
        session = await redis_client.get_ussd_session(ussd_request.session_id)
        
        if ussd_request.session_state == USSDState.START:
            # New session
            session = {
                "phone": ussd_request.phone,
                "session_id": ussd_request.session_id,
                "state": "main_menu",
                "data": {},
                "language": "en",
            }
            await redis_client.save_ussd_session(ussd_request.session_id, session)
            
            # Show main menu
            response = "🌾 Welcome to AgriConnect!\n"
            response += "1. Register\n"
            response += "2. Sell Produce\n"
            response += "3. Buy Produce\n"
            response += "4. My Account\n"
            response += "5. Help"
            
            return PlainTextResponse(response)
        
        elif ussd_request.session_state == USSDState.CONTINUE:
            # Continue session
            if not session:
                return PlainTextResponse("Session expired. Please dial *333# again.")
            
            # Process based on current state
            user_input = ussd_request.text.split('*')[-1] if ussd_request.text else ''
            
            # Main menu
            if session["state"] == "main_menu":
                if user_input == "1":
                    # Register
                    session["state"] = "register_name"
                    await redis_client.save_ussd_session(ussd_request.session_id, session)
                    return PlainTextResponse("Enter your full name:")
                
                elif user_input == "2":
                    # Sell produce
                    session["state"] = "sell_produce"
                    await redis_client.save_ussd_session(ussd_request.session_id, session)
                    return PlainTextResponse("Enter produce type (e.g., tomatoes):")
                
                elif user_input == "3":
                    # Buy produce
                    session["state"] = "buy_produce"
                    await redis_client.save_ussd_session(ussd_request.session_id, session)
                    return PlainTextResponse("Enter produce type to search (or * for all):")
                
                elif user_input == "4":
                    # My account
                    session["state"] = "account"
                    await redis_client.save_ussd_session(ussd_request.session_id, session)
                    return PlainTextResponse("📋 My Account\n1. View Profile\n2. My Listings\n3. My Orders\n4. Back")
                
                elif user_input == "5":
                    # Help
                    return PlainTextResponse("📖 Commands: SELL, LIST, BID, ACCEPT, PAY, CONFIRM, RATE, PRICE, STATUS")
                
                else:
                    return PlainTextResponse("Invalid option. Try again:\n1. Register\n2. Sell\n3. Buy\n4. Account\n5. Help")
            
            # Register flow
            elif session["state"] == "register_name":
                session["data"]["name"] = user_input
                session["state"] = "register_phone"
                await redis_client.save_ussd_session(ussd_request.session_id, session)
                return PlainTextResponse("Your phone number is registered. Enter NRC number:")
            
            elif session["state"] == "register_phone":
                session["data"]["nrc"] = user_input
                session["state"] = "register_complete"
                await redis_client.save_ussd_session(ussd_request.session_id, session)
                return PlainTextResponse("✅ Registration complete! You're now registered for AgriConnect.")
            
            # Sell flow
            elif session["state"] == "sell_produce":
                session["data"]["produce"] = user_input
                session["state"] = "sell_quantity"
                await redis_client.save_ussd_session(ussd_request.session_id, session)
                return PlainTextResponse("Enter quantity (e.g., 100):")
            
            elif session["state"] == "sell_quantity":
                session["data"]["quantity"] = user_input
                session["state"] = "sell_unit"
                await redis_client.save_ussd_session(ussd_request.session_id, session)
                return PlainTextResponse("Enter unit (kg, ton, bundle):")
            
            elif session["state"] == "sell_unit":
                session["data"]["unit"] = user_input
                session["state"] = "sell_price"
                await redis_client.save_ussd_session(ussd_request.session_id, session)
                return PlainTextResponse("Enter price (e.g., 2500):")
            
            elif session["state"] == "sell_price":
                session["data"]["price"] = user_input
                session["state"] = "sell_district"
                await redis_client.save_ussd_session(ussd_request.session_id, session)
                return PlainTextResponse("Enter district (e.g., Mkushi):")
            
            elif session["state"] == "sell_district":
                session["data"]["district"] = user_input
                # Complete the listing
                data = session["data"]
                listing_id = "123"  # TODO: Create actual listing
                response = f"✅ Listing created! ID: {listing_id}\n"
                response += f"{data['produce']} - {data['quantity']}{data['unit']} - K{data['price']} - {data['district']}"
                session["state"] = "main_menu"
                await redis_client.save_ussd_session(ussd_request.session_id, session)
                return PlainTextResponse(response)
            
            # Buy flow
            elif session["state"] == "buy_produce":
                session["data"]["produce"] = user_input if user_input != '*' else ''
                session["state"] = "buy_listings"
                await redis_client.save_ussd_session(ussd_request.session_id, session)
                return PlainTextResponse("📋 Listings:\n1. Tomatoes - 100kg - K2500 - Mkushi\n2. Maize - 50kg - K1500 - Lusaka\nEnter listing ID to bid:")
            
            elif session["state"] == "buy_listings":
                if user_input:
                    # TODO: Process bid
                    response = f"✅ Bid placed on listing {user_input}!"
                    session["state"] = "main_menu"
                    await redis_client.save_ussd_session(ussd_request.session_id, session)
                    return PlainTextResponse(response)
                else:
                    return PlainTextResponse("Invalid listing ID. Try again.")
            
            else:
                return PlainTextResponse("Invalid option. Please try again.")
        
        elif ussd_request.session_state == USSDState.END:
            # End session
            await redis_client.delete_ussd_session(ussd_request.session_id)
            return PlainTextResponse("Thank you for using AgriConnect. Goodbye!")
        
    except Exception as e:
        logger.error(f"❌ Error processing USSD: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMMAND PROCESSOR
# ============================================================================
async def process_command(parsed: ParsedCommand) -> str:
    """
    Process a parsed command.
    
    This routes the command to the appropriate handler.
    """
    command = parsed.command
    
    if command == Command.HELP:
        return SMSTemplates.get("help", parsed.language)
    
    elif command == Command.SELL:
        return SMSTemplates.get(
            "sell_success",
            parsed.language,
            listing_id="123",
            produce=parsed.args[0] if len(parsed.args) > 0 else "produce",
            quantity=parsed.args[1] if len(parsed.args) > 1 else "0",
            unit=parsed.args[2] if len(parsed.args) > 2 else "kg",
            price=parsed.args[3] if len(parsed.args) > 3 else "0",
            district=parsed.args[4] if len(parsed.args) > 4 else "unknown",
        )
    
    elif command == Command.BID:
        return SMSTemplates.get(
            "bid_success",
            parsed.language,
            amount=parsed.args[1] if len(parsed.args) > 1 else "0",
            listing_id=parsed.args[0] if len(parsed.args) > 0 else "unknown",
        )
    
    elif command == Command.LIST:
        # TODO: Search listings
        return "📋 Listings found:\n1. Tomatoes - 100kg - K2500 - Mkushi\n2. Maize - 50kg - K1500 - Lusaka\nReply BID <id> <amount>"
    
    elif command == Command.ACCEPT:
        return f"✅ Bid {parsed.args[0] if parsed.args else 'unknown'} accepted! Transaction created."
    
    elif command == Command.PAY:
        return f"💰 Payment initiated for transaction {parsed.args[0] if parsed.args else 'unknown'}. Pay via Airtel/MTN/Zamtel."
    
    elif command == Command.CONFIRM:
        return f"✅ Delivery confirmed for transaction {parsed.args[0] if parsed.args else 'unknown'}. Escrow released!"
    
    elif command == Command.RATE:
        return f"⭐ Rating submitted for user {parsed.args[0] if parsed.args else 'unknown'}!"
    
    elif command == Command.PRICE:
        return f"📊 Average price for {parsed.args[0] if parsed.args else 'produce'} in {parsed.args[1] if len(parsed.args) > 1 else 'Zambia'}: K2500/kg"
    
    elif command == Command.STATUS:
        return f"📋 Order {parsed.args[0] if parsed.args else 'unknown'}: Processing"
    
    return "⚠️ Command not implemented yet. Reply HELP for commands."
