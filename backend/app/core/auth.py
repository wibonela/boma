"""
Clerk authentication utilities for FastAPI.

This module provides JWT token verification using Clerk's public keys.
"""

from typing import Optional
from datetime import datetime

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ClerkTokenPayload(BaseModel):
    """
    Clerk JWT token payload structure.

    This represents the decoded claims from a Clerk-issued JWT.
    """
    sub: str  # Clerk user ID (external auth ID)
    iss: str  # Issuer URL
    aud: str  # Audience
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    azp: Optional[str] = None  # Authorized party
    sid: Optional[str] = None  # Session ID

    # Optional user metadata
    email: Optional[str] = None
    phone_number: Optional[str] = None
    email_verified: Optional[bool] = None
    phone_verified: Optional[bool] = None


class ClerkAuth:
    """
    Clerk authentication handler.

    Verifies JWT tokens issued by Clerk using the configured public key.
    """

    def __init__(self):
        """Initialize with Clerk configuration from settings."""
        self.public_key = settings.CLERK_PEM_PUBLIC_KEY
        self.issuer = settings.CLERK_ISSUER_URL
        self.audience = settings.CLERK_AUDIENCE

        if not self.public_key:
            raise ValueError("CLERK_PEM_PUBLIC_KEY is not configured")

        logger.info("ClerkAuth initialized with issuer: %s", self.issuer)

    def verify_token(self, token: str) -> ClerkTokenPayload:
        """
        Verify a Clerk JWT token and return the payload.

        Args:
            token: The JWT token string to verify

        Returns:
            ClerkTokenPayload containing the decoded token claims

        Raises:
            HTTPException: If token is invalid, expired, or verification fails
        """
        try:
            # Decode and verify the JWT
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True,
                }
            )

            logger.debug("Token verified successfully for user: %s", payload.get("sub"))

            return ClerkTokenPayload(**payload)

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error("Token verification error: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Global instance
clerk_auth = ClerkAuth()
