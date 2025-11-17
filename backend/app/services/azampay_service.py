"""
AzamPay Payment Gateway Service
Handles mobile money payments via AzamPay for Tanzania market
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class AzamPayService:
    """Service for AzamPay payment gateway integration"""

    def __init__(self):
        self.client_id = settings.AZAMPAY_CLIENT_ID
        self.client_secret = settings.AZAMPAY_CLIENT_SECRET
        self.app_name = settings.AZAMPAY_APP_NAME
        self.api_url = settings.AZAMPAY_API_URL
        self.webhook_secret = settings.AZAMPAY_WEBHOOK_SECRET

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """
        Get or refresh the AzamPay access token
        Tokens are cached and refreshed automatically when expired
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token

        # Generate new token
        url = "https://authenticator-sandbox.azampay.co.tz/AppRegistration/GenerateToken"

        payload = {
            "appName": self.app_name,
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()

                data = response.json()

                if "data" in data and "accessToken" in data["data"]:
                    self._access_token = data["data"]["accessToken"]
                    # Tokens typically expire in 1 hour, cache for 55 minutes to be safe
                    self._token_expires_at = datetime.utcnow() + timedelta(minutes=55)
                    logger.info("AzamPay access token generated successfully")
                    return self._access_token
                else:
                    logger.error(f"Unexpected token response format: {data}")
                    raise Exception("Failed to extract access token from response")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting AzamPay token: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get AzamPay access token: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting AzamPay access token: {str(e)}")
            raise

    async def initiate_mno_checkout(
        self,
        account_number: str,
        amount: float,
        external_id: str,
        provider: str = "Tigo",
        currency: str = "TZS"
    ) -> Dict[str, Any]:
        """
        Initiate Mobile Network Operator (MNO) checkout

        Args:
            account_number: Customer's mobile number (MSISDN)
            amount: Payment amount
            external_id: Unique transaction reference from your system (booking ID)
            provider: Mobile money provider (Mpesa, Airtel, Tigo, Halopesa, Azampesa)
            currency: Currency code (default TZS)

        Returns:
            Dict containing transaction details and status
        """
        token = await self._get_access_token()
        url = f"{self.api_url}/azampay/mno/checkout"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "accountNumber": account_number,
            "amount": str(amount),  # Convert to string as per API spec
            "currency": currency,
            "externalId": external_id,
            "provider": provider
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=60.0  # MNO checkouts can take time
                )

                data = response.json()

                # Log the response for debugging
                logger.info(f"AzamPay MNO checkout response: {data}")

                if response.status_code == 200:
                    return {
                        "success": data.get("success", False),
                        "transaction_id": data.get("transactionId"),
                        "message": data.get("message"),
                        "status_code": response.status_code
                    }
                elif response.status_code == 400:
                    # Validation errors
                    errors = data.get("errors", {})
                    error_messages = []
                    for field, messages in errors.items():
                        if messages:
                            error_messages.extend(messages)

                    return {
                        "success": False,
                        "message": "; ".join(error_messages) if error_messages else "Validation error",
                        "errors": errors,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "message": data.get("message", "Payment initiation failed"),
                        "status_code": response.status_code
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error initiating AzamPay checkout: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "message": f"Payment gateway error: {str(e)}",
                "status_code": e.response.status_code if hasattr(e, 'response') else 500
            }
        except Exception as e:
            logger.error(f"Error initiating AzamPay checkout: {str(e)}")
            return {
                "success": False,
                "message": f"Payment initiation failed: {str(e)}",
                "status_code": 500
            }

    async def initiate_card_checkout(
        self,
        amount: float,
        external_id: str,
        currency: str = "TZS",
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate Card Payment checkout

        Returns a checkout URL that the customer should be redirected to
        to complete the card payment.

        Args:
            amount: Payment amount
            external_id: Unique transaction reference from your system (booking ID)
            currency: Currency code (default TZS)
            customer_email: Customer's email (optional)
            customer_phone: Customer's phone number (optional)

        Returns:
            Dict containing checkout URL and transaction details
        """
        token = await self._get_access_token()
        url = f"{self.api_url}/azampay/checkout"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "amount": str(amount),
            "currency": currency,
            "externalId": external_id,
        }

        # Add optional customer details if provided
        if customer_email:
            payload["customerEmail"] = customer_email
        if customer_phone:
            payload["customerPhone"] = self.format_phone_number(customer_phone)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )

                data = response.json()
                logger.info(f"AzamPay card checkout response: {data}")

                if response.status_code == 200:
                    return {
                        "success": data.get("success", False),
                        "checkout_url": data.get("checkoutUrl"),  # URL to redirect user to
                        "transaction_id": data.get("transactionId"),
                        "message": data.get("message"),
                        "status_code": response.status_code
                    }
                elif response.status_code == 400:
                    # Validation errors
                    errors = data.get("errors", {})
                    error_messages = []
                    for field, messages in errors.items():
                        if messages:
                            error_messages.extend(messages)

                    return {
                        "success": False,
                        "message": "; ".join(error_messages) if error_messages else "Validation error",
                        "errors": errors,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "message": data.get("message", "Card checkout failed"),
                        "status_code": response.status_code
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error initiating card checkout: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "message": f"Payment gateway error: {str(e)}",
                "status_code": e.response.status_code if hasattr(e, 'response') else 500
            }
        except Exception as e:
            logger.error(f"Error initiating card checkout: {str(e)}")
            return {
                "success": False,
                "message": f"Card checkout failed: {str(e)}",
                "status_code": 500
            }

    async def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify payment status using transaction ID

        Args:
            transaction_id: AzamPay transaction ID

        Returns:
            Dict containing payment verification details
        """
        # Note: AzamPay doesn't have a direct transaction status endpoint in the spec
        # Status updates come via webhooks
        # This method is a placeholder for future implementation
        logger.warning("Payment verification called but not implemented - use webhooks")
        return {
            "success": False,
            "message": "Payment verification via API not available. Use webhook callbacks."
        }

    def verify_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify webhook signature to ensure authenticity

        Args:
            payload: Webhook payload
            signature: Signature from webhook headers

        Returns:
            Boolean indicating if signature is valid
        """
        # TODO: Implement signature verification based on AzamPay webhook documentation
        # For now, we'll rely on the webhook secret
        logger.warning("Webhook signature verification not yet implemented")
        return True

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process AzamPay webhook callback

        Expected webhook payload for successful payment:
        {
            "transactionId": "string",
            "externalId": "string",
            "amount": number,
            "status": "success|failed",
            "message": "string"
        }

        Args:
            payload: Webhook payload from AzamPay

        Returns:
            Dict containing processing result
        """
        try:
            transaction_id = payload.get("transactionId")
            external_id = payload.get("externalId")  # This is our booking ID
            status = payload.get("status")
            amount = payload.get("amount")
            message = payload.get("message")

            logger.info(f"Processing AzamPay webhook for external_id: {external_id}, status: {status}")

            return {
                "success": True,
                "transaction_id": transaction_id,
                "external_id": external_id,
                "status": status,
                "amount": amount,
                "message": message
            }

        except Exception as e:
            logger.error(f"Error processing AzamPay webhook: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

    def get_supported_providers(self) -> list[str]:
        """Get list of supported mobile money providers"""
        return ["Mpesa", "Airtel", "Tigo", "Halopesa", "Azampesa"]

    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number to required format
        Ensures number starts with country code (255 for Tanzania)

        Args:
            phone: Phone number in various formats

        Returns:
            Formatted phone number
        """
        # Remove any spaces, dashes, or special characters
        phone = "".join(filter(str.isdigit, phone))

        # If starts with 0, replace with 255
        if phone.startswith("0"):
            phone = "255" + phone[1:]

        # If doesn't start with 255, prepend it
        if not phone.startswith("255"):
            phone = "255" + phone

        return phone


# Create singleton instance
azampay_service = AzamPayService()
