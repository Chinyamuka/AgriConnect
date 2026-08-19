#!/bin/bash

echo "========================================="
echo "AGRICONNECT COMPLETE FLOW TEST"
echo "========================================="

# Step 1: Create listing
echo ""
echo "1. Creating listing..."
LISTING_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8002/api/v1/listings/?farmer_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "produce_type": "maize",
    "quantity": 200,
    "unit": "kg",
    "price": 1500,
    "latitude": -15.3875,
    "longitude": 28.3228,
    "district": "Lusaka",
    "province": "Lusaka Province"
  }')

echo "Listing Response: $LISTING_RESPONSE"
LISTING_ID=$(echo $LISTING_RESPONSE | jq -r '.id' 2>/dev/null)
echo "✅ Listing ID: $LISTING_ID"

if [ -z "$LISTING_ID" ] || [ "$LISTING_ID" = "null" ]; then
    echo "❌ Failed to create listing"
    exit 1
fi

# Step 2: Place bid
echo ""
echo "2. Placing bid..."
BID_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8003/api/v1/bids/?buyer_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d "{
    \"listing_id\": \"$LISTING_ID\",
    \"amount\": 2000,
    \"message\": \"I want to buy this maize\"
  }")

echo "Bid Response: $BID_RESPONSE"
BID_ID=$(echo $BID_RESPONSE | jq -r '.id' 2>/dev/null)
echo "✅ Bid ID: $BID_ID"

if [ -z "$BID_ID" ] || [ "$BID_ID" = "null" ]; then
    echo "❌ Failed to place bid"
    exit 1
fi

# Step 3: Accept bid
echo ""
echo "3. Accepting bid..."
ACCEPT_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8003/api/v1/bids/$BID_ID/accept?farmer_id=550e8400-e29b-41d4-a716-446655440000")
echo "Accept Response: $ACCEPT_RESPONSE"
TRANSACTION_ID=$(echo $ACCEPT_RESPONSE | jq -r '.transaction_id' 2>/dev/null)
echo "✅ Transaction ID: $TRANSACTION_ID"

if [ -z "$TRANSACTION_ID" ] || [ "$TRANSACTION_ID" = "null" ]; then
    echo "❌ Failed to accept bid"
    exit 1
fi

# Step 4: Initiate payment
echo ""
echo "4. Initiating payment with Flutterwave..."
PAYMENT_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8004/api/v1/payments/initiate" \
  -H "Content-Type: application/json" \
  -d "{
    \"bid_id\": \"$BID_ID\",
    \"amount\": 2000,
    \"payment_method\": \"airtel_money\",
    \"phone_number\": \"+260977880000\"
  }")

echo "Payment Response: $PAYMENT_RESPONSE"
FLUTTERWAVE_REF=$(echo $PAYMENT_RESPONSE | jq -r '.flutterwave_reference' 2>/dev/null)
TRANSACTION_ID=$(echo $PAYMENT_RESPONSE | jq -r '.transaction_id' 2>/dev/null)

echo ""
echo "✅ Flutterwave Reference: $FLUTTERWAVE_REF"
echo "✅ Transaction ID: $TRANSACTION_ID"

echo ""
echo "========================================="
echo "📝 INSTRUCTIONS:"
echo "========================================="
echo "1. Go to: https://dashboard.flutterwave.com/"
echo "2. Click Transactions"
echo "3. Find the transaction with reference: $FLUTTERWAVE_REF"
echo "4. Click 'Simulate' to complete the payment"
echo "5. Enter OTP: 12345"
echo "6. Wait for webhook to be received"
echo "7. Then run:"
echo "   curl -X POST http://127.0.0.1:8004/api/v1/payments/confirm -H 'Content-Type: application/json' -d '{\"transaction_id\":\"$TRANSACTION_ID\"}'"
echo "========================================="
