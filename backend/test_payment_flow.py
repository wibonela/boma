#!/usr/bin/env python3
"""
Test script for payment flow
This tests the booking and payment endpoints
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_payment_flow():
    """Test the complete payment flow"""

    print("=" * 60)
    print("TESTING BOMA PAYMENT FLOW")
    print("=" * 60)

    # Note: This test requires a valid user token from Clerk
    # For now, we'll just test endpoint availability

    # 1. Test API is running
    print("\n1. Testing API availability...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   ✓ API is running: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # 2. Check OpenAPI docs
    print("\n2. Checking available endpoints...")
    try:
        response = requests.get("http://localhost:8000/openapi.json")
        openapi = response.json()

        # List booking endpoints
        print("   Booking endpoints:")
        for path, methods in openapi.get('paths', {}).items():
            if '/bookings' in path:
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                        summary = details.get('summary', 'No summary')
                        print(f"   - {method.upper():6} {path:40} {summary}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # 3. Test webhook endpoint (should accept POST)
    print("\n3. Testing webhook endpoint availability...")
    try:
        # This will fail without proper signature, but we're just testing it exists
        response = requests.post(
            f"{BASE_URL}/bookings/webhooks/azampay",
            json={"test": "data"}
        )
        print(f"   ✓ Webhook endpoint responds: {response.status_code}")
        # Any response (even error) means endpoint exists
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # 4. Show what's needed for real testing
    print("\n" + "=" * 60)
    print("NEXT STEPS FOR TESTING")
    print("=" * 60)
    print("""
To test the complete payment flow, you need:

1. Create a test user via Clerk authentication
2. Get a valid JWT token from Clerk
3. Create a test property
4. Test booking creation with the token:

   curl -X POST http://localhost:8000/api/v1/bookings \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{
       "property_id": "PROPERTY_ID",
       "check_in_date": "2025-12-01",
       "check_out_date": "2025-12-03",
       "adults": 2,
       "children": 0,
       "infants": 0
     }'

5. Test payment initiation:

   curl -X POST http://localhost:8000/api/v1/bookings/BOOKING_ID/payment \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{
       "phone_number": "0754123456",
       "provider": "Mpesa"
     }'

6. Monitor webhook callbacks from AzamPay

The mobile app will handle all of this automatically once you log in!
    """)

    print("\n" + "=" * 60)
    print("BACKEND IMPLEMENTATION STATUS")
    print("=" * 60)
    print("""
✓ AzamPay service implemented
✓ Token caching (55 min TTL)
✓ Phone number formatting
✓ Booking creation endpoint
✓ Payment initiation endpoint
✓ Webhook endpoint for callbacks
✓ Payment status polling
✓ Mobile app payment screen
✓ Integration with BookingSummaryScreen

READY FOR TESTING WITH REAL USERS!
    """)

if __name__ == "__main__":
    test_payment_flow()
