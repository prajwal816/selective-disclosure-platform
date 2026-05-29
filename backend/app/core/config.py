"""
Application configuration using Pydantic Settings.
Loads environment variables with validation and type coercion.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "VeriCred Share"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # ── Server ───────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/vericred",
        description="Async PostgreSQL connection string",
    )

    # ── JWT Authentication ───────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-64",
        description="Secret key for JWT token signing",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Ed25519 Cryptographic Keys ───────────────────────────────
    ED25519_PRIVATE_KEY_HEX: str = Field(
        default="",
        description="Hex-encoded Ed25519 private key seed (32 bytes). Auto-generated if empty.",
    )
    ISSUER_DID: str = Field(
        default="did:vericred:issuer:primary",
        description="Decentralized Identifier for the credential issuer",
    )

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_VERIFY: str = "20/minute"
    RATE_LIMIT_SHARE: str = "30/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    # ── Share Links ──────────────────────────────────────────────
    DEFAULT_SHARE_EXPIRY_HOURS: int = 24
    MAX_SHARE_EXPIRY_DAYS: int = 30
    MAX_SHARE_ACCESS_COUNT: int = 100

    # ── Frontend URL (for generating share links) ────────────────
    FRONTEND_URL: str = "http://localhost:3000"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — parsed once at startup."""
    return Settings()
