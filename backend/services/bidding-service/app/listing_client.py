"""
================================================================================
LISTING SERVICE HTTP CLIENT
================================================================================

This module handles communication with the Listing Service.

Why call Listing Service?
1. Validate listing exists before placing a bid
2. Check listing status (must be 'active')
3. Get farmer_id from the listing
4. Decoupled communication via HTTP API

Why not direct database access?
1. Database-per-service pattern - each service has its own database
2. Decoupling - Listing Service is the source of truth for listings
3. If we change the listing schema, only Listing Service needs to change
4. Better isolation - failures are contained

================================================================================
"""
import httpx
from typing import Optional, Dict, Any
from uuid import UUID
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ListingClient:
    """
    HTTP client for the Listing Service.
    
    Handles communication with the Listing Service API.
    """
    
    def __init__(self):
        """Initialize the HTTP client."""
        self.base_url = settings.listing_service_url
        self.timeout = 10.0  # seconds
    
    async def get_listing(self, listing_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a listing by ID from the Listing Service.
        
        Args:
            listing_id: UUID of the listing
        
        Returns:
            Dict: Listing data, or None if not found
        
        Raises:
            Exception: If the Listing Service is unavailable
        """
        url = f"{self.base_url}/api/v1/listings/{listing_id}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Listing {listing_id} found")
                    return data
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Listing {listing_id} not found")
                    return None
                else:
                    logger.error(f"❌ Listing Service error: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"❌ Listing Service timeout: {listing_id}")
            raise Exception("Listing Service is unavailable (timeout)")
        except httpx.ConnectError:
            logger.error(f"❌ Cannot connect to Listing Service")
            raise Exception("Listing Service is unavailable (connection refused)")
        except Exception as e:
            logger.error(f"❌ Error getting listing: {str(e)}")
            raise
    
    async def update_listing_status(
        self,
        listing_id: UUID,
        status: str,
        farmer_id: UUID,
    ) -> bool:
        """
        Update the status of a listing (mark as sold).
        
        This is called when a bid is accepted.
        
        Args:
            listing_id: UUID of the listing
            status: New status ('sold')
            farmer_id: ID of the farmer (for ownership check)
        
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.base_url}/api/v1/listings/{listing_id}"
        params = {"farmer_id": str(farmer_id)}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    url,
                    params=params,
                    json={"status": status}
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Listing {listing_id} marked as {status}")
                    return True
                else:
                    logger.error(f"❌ Failed to update listing: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error updating listing: {str(e)}")
            return False


# Create a singleton instance
listing_client = ListingClient()
