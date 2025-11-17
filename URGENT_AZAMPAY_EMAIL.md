# URGENT: AzamPay Sandbox Account Locked - 423 Error

**To**: support@azampay.co.tz
**CC**: developers@azampay.co.tz
**Subject**: URGENT: Sandbox Account Locked (423 Error) - Client ID: ed3c0530-f27a-4faa-b9f4-fd838418f8de

---

Dear AzamPay Support Team,

We are experiencing a **critical blocker** with our AzamPay sandbox integration. Our token generation endpoint is returning **HTTP 423 Locked** status.

## Error Details

**Endpoint**: `https://authenticator-sandbox.azampay.co.tz/AppRegistration/GenerateToken`
**Error**: `Client error '423 Locked'`
**Time**: November 16, 2025 - 06:22 AM EAT

### Request Payload:
```json
{
  "appName": "boma",
  "clientId": "ed3c0530-f27a-4faa-b9f4-fd838418f8de",
  "clientSecret": "EMWixrJKcYrg44CEHK/0ne..."
}
```

### Our Credentials:
- **App Name**: boma
- **Client ID**: ed3c0530-f27a-4faa-b9f4-fd838418f8de
- **Environment**: Sandbox
- **Integration**: Mobile Money (M-Pesa, Airtel, Tigo, Halopesa)

## What We've Implemented

✅ Full booking system with payment integration
✅ Webhook endpoint ready
✅ Phone number: +255655808858 (for STK push testing)
✅ All code tested and working

**We are blocked ONLY by the 423 error on your token endpoint.**

## Urgent Questions

1. **Is our sandbox account activated?**
2. **Do we need to complete KYC/verification for sandbox?**
3. **Are there IP restrictions blocking our requests?**
4. **Is there a rate limit we exceeded?**
5. **Should we regenerate credentials in the dashboard?**

## Business Impact

We are launching **BOMA Property Rentals** platform in **2 weeks**. This blocker is preventing us from testing the complete payment flow.

We need this resolved within **24-48 hours** to stay on schedule.

## What We Need

Please **urgently**:
1. ✅ Unlock/activate our sandbox account
2. ✅ Confirm our credentials are valid
3. ✅ Provide test phone numbers if needed
4. ✅ Share any missing configuration steps

## Alternative Request

If sandbox activation takes time, please provide:
- **Production credentials** for early testing
- **Card payment** integration as backup
- **Direct contact** of technical team for faster resolution

## Contact Information

- **Company**: BOMA Property Rentals
- **Developer**: [Your Name]
- **Email**: [Your Email]
- **Phone**: +255655808858
- **Website**: boma.co.tz (launching soon)

We're ready to jump on a call immediately if needed.

Thank you for your urgent assistance.

Best regards,
BOMA Development Team

---

**P.S.**: Our complete integration code is ready and tested. We just need the 423 lock removed to proceed.
