"""
Rate limiting configuration using SlowAPI.
Provides per-endpoint rate limiting with configurable limits.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# ── Limiter Instance ─────────────────────────────────────────────
# Uses client IP for rate limit tracking
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://",
)
