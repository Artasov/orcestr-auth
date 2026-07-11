"""Reusable authentication primitives and framework adapters."""

from .config import AuthConfig, CookieConfig, OAuthClientConfig
from .passwords import hash_password, verify_and_update_password, verify_password
from .ports import AuditSink, Clock, RateLimiter, UserRepository
from .tokens import TokenCodec, TokenPayloadError

__all__ = [
    "AuthConfig",
    "AuditSink",
    "Clock",
    "CookieConfig",
    "OAuthClientConfig",
    "RateLimiter",
    "TokenCodec",
    "TokenPayloadError",
    "UserRepository",
    "hash_password",
    "verify_and_update_password",
    "verify_password",
]
