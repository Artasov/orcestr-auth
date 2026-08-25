from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class OAuthClientConfig:
    client_id: str
    client_secret: str
    redirect_origins: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OAuth2ClientConfig:
    """Registered public client for the OAuth 2.1 authorization server."""

    display_name: str
    redirect_uris: tuple[str, ...]
    scopes: tuple[str, ...] = ()
    enabled: bool = True
    pkce_required: bool = True


@dataclass(frozen=True, slots=True)
class CookieConfig:
    access_name: str = "orcestr_access"
    refresh_name: str = "orcestr_refresh"
    secure: bool = True
    same_site: Literal["lax", "strict", "none"] = "lax"
    domain: str | None = None
    path: str = "/"


@dataclass(frozen=True, slots=True)
class AuthConfig:
    secret_key: str
    issuer: str = "orcestr"
    audience: str = "orcestr-api"
    algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    websocket_ticket_seconds: int = 60
    verification_code_minutes: int = 15
    verification_code_length: int = 6
    verification_max_attempts: int = 5
    verification_resend_cooldown_seconds: int = 60
    password_reset_code_minutes: int = 15
    password_reset_code_length: int = 6
    password_reset_max_attempts: int = 5
    password_reset_resend_cooldown_seconds: int = 60
    oauth2_authorization_code_seconds: int = 120
    cookie: CookieConfig = field(default_factory=CookieConfig)
    oauth: dict[str, OAuthClientConfig] = field(default_factory=dict)
    oauth2_clients: dict[str, OAuth2ClientConfig] = field(default_factory=dict)

    @property
    def enabled_oauth_providers(self) -> tuple[str, ...]:
        return tuple(
            provider
            for provider in ("github", "google", "yandex")
            if provider in self.oauth
        )
