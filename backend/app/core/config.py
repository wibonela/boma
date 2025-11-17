"""
Core configuration module for BOMA application.
Reads from environment variables and provides typed configuration.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "BOMA"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:19006",
        "http://localhost:19000",
        "http://localhost:8081",
        "exp://localhost:19000",
        "exp://localhost:8081",
        "*"  # Allow all origins in development (remove in production)
    ]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Local File Storage
    UPLOAD_DIR: str = "uploads"
    STATIC_URL: str = "/static"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Payment - AzamPay
    AZAMPAY_CLIENT_ID: str
    AZAMPAY_CLIENT_SECRET: str
    AZAMPAY_APP_NAME: str = "BOMA"
    AZAMPAY_API_URL: str = "https://sandbox.azampay.co.tz"
    AZAMPAY_WEBHOOK_SECRET: str

    # Payment - Selcom (Optional - only required if using Selcom)
    SELCOM_API_KEY: Optional[str] = None
    SELCOM_API_SECRET: Optional[str] = None
    SELCOM_VENDOR_ID: Optional[str] = None
    SELCOM_API_URL: str = "https://apigw.selcommobile.com"
    SELCOM_WEBHOOK_SECRET: Optional[str] = None

    # Email (Simple SMTP for now - can be configured later)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@boma.co.tz"
    SMTP_FROM_NAME: str = "BOMA"

    # Localization
    DEFAULT_COUNTRY: str = "TZ"
    DEFAULT_CURRENCY: str = "TZS"
    DEFAULT_TIMEZONE: str = "Africa/Dar_es_Salaam"
    SUPPORTED_COUNTRIES: List[str] = ["TZ"]
    SUPPORTED_CURRENCIES: List[str] = ["TZS"]

    # Business Rules
    PLATFORM_FEE_PERCENTAGE: float = 15.0
    BOOKING_EXPIRY_MINUTES: int = 30
    DEPOSIT_HOLD_DAYS: int = 7
    MINIMUM_BOOKING_HOURS: int = 4
    MAXIMUM_ADVANCE_BOOKING_DAYS: int = 365

    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]
    ALLOWED_DOCUMENT_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png"]

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Admin
    ADMIN_EMAIL: str = "admin@boma.co.tz"
    ADMIN_INITIAL_PASSWORD: str = "changeme"

    # Monitoring (optional - can add Sentry later)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins if provided as string."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @field_validator("SUPPORTED_COUNTRIES", "SUPPORTED_CURRENCIES", mode="before")
    @classmethod
    def parse_lists(cls, v):
        """Parse list fields if provided as string."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Global settings instance
settings = Settings()
