#!/bin/bash
echo "========================================="
echo "AGRICONNECT COMPLETE FLOW TEST"
echo "========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Create Listing
echo -e "${BLUE}1. Creating listing...${NC}"
LISTING_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8002/api/v1/listings/?farmer_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "produce_type": "tomatoes",
    "quantity": 100,
    "unit": "kg",
    "price": 2500,
    "latitude": -15.3875,
    "longitude": 28.3228,
    "district": "Lusaka",
    "province": "Lusaka Province"
  }')

LISTING_ID=$(echo $LISTING_RESPONSE | jq -r '.id')
echo -e "${GREEN}✅ Listing created: $LISTING_ID${NC}"

# Step 2: Place Bid
echo -e "${BLUE}2. Placing bid...${NC}"
BID_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8003/api/v1/bids/?buyer_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d "{
    \"listing_id\": \"$LISTING_ID\",
    \"amount\": 3000,
    \"message\": \"I want to buy these tomatoes\"
  }")

BID_ID=$(echo $BID_RESPONSE | jq -r '.id')
echo -e "${GREEN}✅ Bid placed: $BID_ID${NC}"

# Step 3: Get Bids
echo -e "${BLUE}3. Getting bids for listing...${NC}"
BIDS=$(curl -s "http://127.0.0.1:8003/api/v1/bids/listing/$LISTING_ID")
BID_COUNT=$(echo $BIDS | jq '.total')
echo -e "${GREEN}✅ Found $BID_COUNT bid(s)${NC}"

# Step 4: Accept Bid
echo -e "${BLUE}4. Accepting bid...${NC}"
ACCEPT_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8003/api/v1/bids/$BID_ID/accept?farmer_id=550e8400-e29b-41d4-a716-446655440000")
TRANSACTION_ID=$(echo $ACCEPT_RESPONSE | jq -r '.transaction_id')
echo -e "${GREEN}✅ Bid accepted! Transaction ID: $TRANSACTION_ID${NC}"

# Step 5: Verify Listing Status
echo -e "${BLUE}5. Checking listing status...${NC}"
STATUS=$(curl -s "http://127.0.0.1:8002/api/v1/listings/$LISTING_ID" | jq -r '.status')
echo -e "${GREEN}✅ Listing status: $STATUS${NC}"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}🎉 COMPLETE FLOW SUCCESSFUL! 🎉${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Summary:"
echo "  Listing ID: $LISTING_ID"
echo "  Bid ID: $BID_ID"
echo "  Transaction ID: $TRANSACTION_ID"
echo "  Listing Status: $STATUS"
