"""
Data models for the Messaging Gateway Service.

These define the structure of incoming and outgoing data.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================
class MessageType(str, Enum):
    """Type of incoming message."""
    SMS = "sms"
    USSD = "ussd"


class USSDState(str, Enum):
    """State of a USSD session."""
    START = "start"
    CONTINUE = "continue"
    END = "end"


class Command(str, Enum):
    """
    SMS commands supported by AgriConnect.
    
    These are the keywords users type in SMS/USSD.
    """
    SELL = "SELL"          # Create a listing
    LIST = "LIST"          # Search listings
    BID = "BID"            # Place a bid
    ACCEPT = "ACCEPT"      # Accept a bid
    PAY = "PAY"            # Make a payment
    CONFIRM = "CONFIRM"    # Confirm delivery
    RATE = "RATE"          # Rate a user
    PRICE = "PRICE"        # Get price index
    HELP = "HELP"          # Show help
    STATUS = "STATUS"      # Check order status


class Language(str, Enum):
    """
    Supported languages for SMS templates.
    
    Zambia's 4 most common local languages.
    """
    ENGLISH = "en"
    NYANJA = "ny"
    BEMBA = "bem"
    TONGA = "toi"
    LOZI = "loz"


# ============================================================================
# REQUEST MODELS
# ============================================================================
class SMSWebhookRequest(BaseModel):
    """
    Request from Africa's Talking SMS webhook.
    
    This is the data Africa's Talking sends when an SMS is received.
    """
    phone: str = Field(..., description="Sender's phone number")
    text: str = Field(..., description="SMS text content")
    network: Optional[str] = Field(None, description="Mobile network")
    timestamp: Optional[str] = Field(None, description="Timestamp of SMS")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    @validator('phone')
    def validate_phone(cls, v):
        """Ensure phone number starts with + and has valid format."""
        if not v.startswith('+'):
            v = '+' + v
        return v


class USSDWebhookRequest(BaseModel):
    """
    Request from Africa's Talking USSD webhook.
    
    This is the data Africa's Talking sends for USSD sessions.
    """
    phone: str = Field(..., description="User's phone number")
    session_id: str = Field(..., description="USSD session ID")
    session_state: USSDState = Field(..., description="Session state")
    text: str = Field(..., description="User's input")
    network: Optional[str] = Field(None, description="Mobile network")
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v.startswith('+'):
            v = '+' + v
        return v


class ParsedCommand(BaseModel):
    """
    Parsed SMS command.
    
    After parsing the raw SMS text, we extract:
    - The command (SELL, LIST, etc.)
    - The arguments (produce, quantity, price, etc.)
    - The user's phone number
    """
    command: Command
    args: List[str] = Field(default_factory=list)
    phone: str
    raw_text: str
    language: Language = Language.ENGLISH


# ============================================================================
# RESPONSE MODELS
# ============================================================================
class SMSResponse(BaseModel):
    """
    Response from the messaging gateway.
    
    When the gateway processes an SMS, it returns this.
    """
    success: bool
    message: str
    command: Optional[Command] = None
    user_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class USSDResponse(BaseModel):
    """
    Response for USSD session.
    
    This is what the gateway sends back to Africa's Talking.
    """
    response: str = Field(..., description="Message to show to user")
    session_state: USSDState = Field(..., description="End or continue session")
    menu: Optional[List[str]] = None


# ============================================================================
# EVENT MODELS (for Kafka)
# ============================================================================
class SMSReceivedEvent(BaseModel):
    """
    Event published when an SMS is received.
    
    Other services (Fraud Service, User Service) listen to this.
    """
    event_type: str = "sms.received"
    phone: str
    text: str
    command: str
    args: List[str]
    language: str
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = None


class USSDUpdatedEvent(BaseModel):
    """
    Event published when a USSD session is updated.
    """
    event_type: str = "ussd.session.updated"
    phone: str
    session_id: str
    state: str
    input: str
    timestamp: datetime = Field(default_factory=datetime.now)
