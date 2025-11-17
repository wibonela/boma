# Email to AzamPay Support

**Subject**: AzamPay Integration Support - BOMA Property Rental Platform

---

Dear AzamPay Developer Support Team,

We are integrating AzamPay's payment gateway into **BOMA**, a property rental platform for Tanzania. We have successfully implemented the mobile money checkout flow but are experiencing issues with payment completion. We need your assistance to identify if there are configuration issues on your end.

## What We've Implemented

### ✅ Successfully Completed:
1. **Authentication**: Token generation working (`/AppRegistration/GenerateToken`)
2. **Checkout Initiation**: MNO checkout endpoint integrated (`/azampay/mno/checkout`)
3. **Webhook Endpoint**: Created and ready to receive callbacks
4. **Booking System**: Full booking creation flow with `AWAITING_PAYMENT` status

### 🔄 Current Status:
- Mobile money checkout requests are being sent successfully
- Transactions are initiated with unique external IDs
- However, we're not receiving successful responses or webhook callbacks

## Technical Implementation Details

### Our Setup:
- **Environment**: Sandbox
- **App Name**: `boma`
- **Client ID**: `ed3c0530-f27a-4faa-b9f4-fd838418f8de`
- **API Endpoint**: `https://sandbox.azampay.co.tz`
- **Webhook URL**: `https://fungicidally-uninfective-neville.ngrok-free.dev/api/v1/bookings/webhooks/azampay`

### Code Implementation:
```python
# Token Generation (Working)
async def _get_access_token(self) -> str:
    url = "https://authenticator-sandbox.azampay.co.tz/AppRegistration/GenerateToken"
    payload = {
        "appName": self.app_name,
        "clientId": self.client_id,
        "clientSecret": self.client_secret
    }
    # Token cached for 55 minutes
    response = await client.post(url, json=payload, timeout=30.0)
    data = response.json()
    return data["data"]["accessToken"]

# MNO Checkout (Initiated but not completing)
async def initiate_mno_checkout(
    self,
    account_number: str,  # Phone: +255655808858
    amount: float,        # e.g., 22000.00 TZS
    external_id: str,     # Unique booking ID
    provider: str = "Mpesa"
) -> Dict[str, Any]:
    token = await self._get_access_token()
    url = f"{self.api_url}/azampay/mno/checkout"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "accountNumber": account_number,
        "amount": str(amount),
        "currency": "TZS",
        "externalId": external_id,
        "provider": provider
    }

    response = await client.post(url, json=payload, headers=headers, timeout=60.0)
    return response.json()
```

### Webhook Handler:
```python
@router.post("/webhooks/azampay")
async def azampay_webhook(request: Request, db: AsyncSession):
    raw_body = await request.json()

    # Expected fields: transactionId, externalId, amount, status
    external_id = raw_body.get("externalId")  # Our booking ID
    status = raw_body.get("status")            # success/failed
    transaction_id = raw_body.get("transactionId")

    # Update booking and payment records
    # Send notifications
    # Trigger confirmation emails

    return {"status": "received"}
```

## Issues We're Experiencing

### 1. **No STK Push Received**
- Phone number: `+255655808858` (Vodacom M-Pesa)
- No payment prompt appearing on the phone
- Tested with amounts: 22,000 TZS, 10,000 TZS

### 2. **No Webhook Callbacks**
- Webhook URL configured: `https://fungicidally-uninfective-neville.ngrok-free.dev/api/v1/bookings/webhooks/azampay`
- Endpoint is publicly accessible and tested
- No callbacks received even after checkout initiation

### 3. **Unclear Response Status**
- Need clarification on expected response structure from `/azampay/mno/checkout`
- What does success look like?
- What error codes should we handle?

## Questions for Your Team

1. **Callback URL Configuration**:
   - Do we need to manually add our webhook URL in the AzamPay dashboard?
   - Is there a specific callback URL format required?
   - Should we whitelist our ngrok domain?

2. **Phone Number Format**:
   - We're using: `+255655808858`
   - Should it be: `255655808858` or `0655808858`?
   - Is there a specific format for different providers (M-Pesa, Airtel, Tigo, Halopesa)?

3. **Sandbox Testing**:
   - Are sandbox transactions actually triggering real STK pushes?
   - Or is there a test mode that simulates successful payments?
   - What test phone numbers should we use?

4. **Transaction Status**:
   - How long should we wait for a payment response?
   - Should we implement polling in addition to webhooks?
   - What's the maximum timeout before marking a transaction as failed?

5. **Error Handling**:
   - What are the common error codes we should handle?
   - Documentation on error responses would be helpful

## What We Need from You

1. **Verify our sandbox credentials** are active and properly configured
2. **Confirm our webhook URL** is registered in your system
3. **Provide sample success/failure webhook payloads** for testing
4. **Clarify the correct phone number format** for Tanzanian mobile numbers
5. **Share any sandbox-specific configurations** we might be missing

## Alternative: Card Payment Integration

If mobile money continues to have issues, we're also interested in implementing your **card payment** integration as a backup. Please provide:
- Card payment API documentation
- Required credentials/setup
- Testing procedure

## Our Timeline

We're targeting to launch BOMA within the next 2 weeks. Quick resolution of these issues would be greatly appreciated.

## Contact Information

- **Company**: BOMA Property Rentals
- **Developer**: [Your Name]
- **Email**: [Your Email]
- **Phone**: +255655808858
- **Integration Environment**: Sandbox (transitioning to Production upon resolution)

Thank you for your assistance. We're excited to integrate AzamPay as our primary payment gateway for the Tanzanian market.

Best regards,
BOMA Development Team

---

**Attachments**:
- API request/response logs (if needed)
- Webhook endpoint code
- Error screenshots

