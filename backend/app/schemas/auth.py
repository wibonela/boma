"""
Authentication request/response schemas.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=15)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: Optional[str] = "guest"  # guest, host, or both

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @validator('phone_number')
    def validate_phone(cls, v):
        """Validate Tanzania phone number format."""
        # Remove any spaces or dashes
        phone = re.sub(r'[\s\-]', '', v)

        # Check if it's a valid Tanzania number
        if not (phone.startswith('255') or phone.startswith('0')):
            raise ValueError('Phone number must start with 255 or 0')

        if phone.startswith('255') and len(phone) != 12:
            raise ValueError('Phone number with 255 must be 12 digits')

        if phone.startswith('0') and len(phone) != 10:
            raise ValueError('Phone number with 0 must be 10 digits')

        return phone


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordChange(BaseModel):
    """Schema for password change (authenticated user)."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(BaseModel):
    """Schema for user response (excluding sensitive data)."""
    id: str
    email: str
    phone_number: str
    full_name: str
    email_verified: bool
    is_active: bool
    role: str
    created_at: str

    class Config:
        from_attributes = True
