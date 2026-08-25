from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import re
import secrets
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import AuthConfig, OAuth2ClientConfig
from ..contracts import (
    OAuth2AuthorizationContext,
    OAuth2AuthorizationRequest,
    OAuth2AuthorizationResponse,
    OAuth2TokenRequest,
    OAuth2TokenResponse,
)
from ..ports import UserRepository
from ..sqlalchemy import AuthModelSet
from .sessions import AuthSessionError, AuthSessionService, aware_utc

_PKCE_CHALLENGE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_PKCE_VERIFIER = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")
_SCOPE_TOKEN = re.compile(r'^[\x21\x23-\x5B\x5D-\x7E]+$')
_NATIVE_SCHEME = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:\.[a-z][a-z0-9]*(?:-[a-z0-9]+)*){2,}$"
)
_NATIVE_AUTHORITY = re.compile(r"^[A-Za-z0-9._~-]+$")
_INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_ENCODED_CONTROL = re.compile(r"%(?:0[0-9A-Fa-f]|1[0-9A-Fa-f]|7F)", re.IGNORECASE)
_FORBIDDEN_REDIRECT_SCHEMES = frozenset(
    {"javascript", "data", "file", "blob", "about", "vbscript"}
)


def validate_oauth2_redirect_uri(uri: str) -> None:
    """Validate an absolute redirect URI allowed for a public/native client.

    HTTPS is accepted for hosted clients, HTTP is restricted to loopback hosts,
    and native schemes must use a lower-case reverse-domain identifier.
    Exact registration matching is enforced separately by the authorization
    service.
    """

    if (
        not uri
        or len(uri) > 2048
        or "\\" in uri
        or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in uri)
        or _INVALID_PERCENT_ESCAPE.search(uri)
        or _ENCODED_CONTROL.search(uri)
    ):
        raise ValueError("Invalid OAuth2 redirect URI.")
    try:
        redirect = urlsplit(uri)
        port = redirect.port
        username = redirect.username
        password = redirect.password
        hostname = redirect.hostname
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid OAuth2 redirect URI.") from exc

    scheme = redirect.scheme.lower()
    if (
        not scheme
        or scheme in _FORBIDDEN_REDIRECT_SCHEMES
        or redirect.fragment
        or username is not None
        or password is not None
    ):
        raise ValueError("Invalid OAuth2 redirect URI.")

    if scheme == "https":
        if not redirect.netloc or not hostname:
            raise ValueError("HTTPS OAuth2 redirects require a host.")
        return

    if scheme == "http":
        if not redirect.netloc or not hostname:
            raise ValueError("HTTP OAuth2 redirects require a loopback host.")
        loopback = hostname.lower() == "localhost"
        if not loopback:
            try:
                loopback = ipaddress.ip_address(hostname).is_loopback
            except ValueError:
                loopback = False
        if not loopback:
            raise ValueError("HTTP OAuth2 redirects are restricted to loopback hosts.")
        return

    if not _NATIVE_SCHEME.fullmatch(redirect.scheme):
        raise ValueError("Native OAuth2 redirects require a reverse-domain scheme.")
    if port is not None:
        raise ValueError("Native OAuth2 redirects must not specify a port.")
    if redirect.netloc:
        if not _NATIVE_AUTHORITY.fullmatch(redirect.netloc):
            raise ValueError("Invalid native OAuth2 redirect authority.")
    elif not redirect.path.startswith("/"):
        raise ValueError("Native OAuth2 redirects require an absolute callback path.")
    if not redirect.netloc and not redirect.path:
        raise ValueError("Native OAuth2 redirects require a callback target.")


class OAuth2ErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    INVALID_CLIENT = "invalid_client"
    INVALID_GRANT = "invalid_grant"
    UNAUTHORIZED_CLIENT = "unauthorized_client"
    UNSUPPORTED_GRANT_TYPE = "unsupported_grant_type"
    UNSUPPORTED_RESPONSE_TYPE = "unsupported_response_type"
    INVALID_SCOPE = "invalid_scope"
    ACCESS_DENIED = "access_denied"
    SERVER_ERROR = "server_error"


class OAuth2ProtocolError(ValueError):
    def __init__(
        self,
        error: OAuth2ErrorCode,
        description: str,
        *,
        status_code: int = 400,
    ) -> None:
        super().__init__(error.value)
        self.error = error
        self.description = description
        self.status_code = status_code


class OAuth2AuthorizationService:
    """OAuth 2.1 Authorization Code + PKCE service for public clients."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        models: AuthModelSet,
        users: UserRepository,
        config: AuthConfig,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        code_factory: Callable[[], str] = lambda: secrets.token_urlsafe(48),
    ) -> None:
        if models.authorization_code is None:
            raise ValueError(
                "OAuth2AuthorizationService requires authorization-code models."
            )
        self.db = session
        self.models = models
        self.authorization_code_model = models.authorization_code
        self.users = users
        self.config = config
        self.now = now
        self.code_factory = code_factory
        self.sessions = AuthSessionService(
            session,
            models=models,
            users=users,
            config=config,
            now=now,
        )

    def context(
        self,
        payload: OAuth2AuthorizationRequest,
    ) -> OAuth2AuthorizationContext:
        client = self._client(payload.client_id)
        self._validate_authorization_request(payload, client)
        scopes = self._scopes(payload.scope, client)
        return OAuth2AuthorizationContext(
            client_id=payload.client_id,
            display_name=client.display_name,
            redirect_uri=payload.redirect_uri,
            requested_scopes=scopes,
            state=payload.state,
            code_challenge=payload.code_challenge,
        )

    async def authorize(
        self,
        payload: OAuth2AuthorizationRequest,
        user: Any,
    ) -> OAuth2AuthorizationResponse:
        context = self.context(payload)
        if not self.users.is_active(user):
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.ACCESS_DENIED,
                "The resource owner cannot authorize this client.",
            )
        raw_code = self.code_factory()
        if not 32 <= len(raw_code) <= 512:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.SERVER_ERROR,
                "The authorization server could not issue a code.",
                status_code=500,
            )
        now = aware_utc(self.now())
        lifetime = self.config.oauth2_authorization_code_seconds
        if not 1 <= lifetime <= 600:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.SERVER_ERROR,
                "The authorization code lifetime is misconfigured.",
                status_code=500,
            )
        self.db.add(
            self.authorization_code_model(
                id=str(uuid4()),
                user_id=self.users.user_id(user),
                code_hash=self.hash_value(raw_code),
                state_hash=self.hash_value(context.state),
                client_id=context.client_id,
                redirect_uri=context.redirect_uri,
                scope=" ".join(context.requested_scopes),
                code_challenge=context.code_challenge,
                code_challenge_method="S256",
                expires_at=now + timedelta(seconds=lifetime),
            )
        )
        await self.db.flush()
        return OAuth2AuthorizationResponse(
            redirect_uri=self._authorization_redirect(
                context.redirect_uri,
                code=raw_code,
                state=context.state,
            )
        )

    async def token(
        self,
        payload: OAuth2TokenRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> OAuth2TokenResponse:
        if payload.grant_type == "authorization_code":
            return await self._exchange_authorization_code(
                payload,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        if payload.grant_type == "refresh_token":
            return await self._exchange_refresh_token(
                payload,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        raise OAuth2ProtocolError(
            OAuth2ErrorCode.UNSUPPORTED_GRANT_TYPE,
            "Only authorization_code and refresh_token grants are supported.",
        )

    async def revoke(self, *, client_id: str, token: str) -> bool:
        self._client(client_id)
        revoked = await self.sessions.revoke(
            token,
            oauth_client_id=client_id,
            commit=False,
        )
        await self.db.flush()
        return revoked

    async def _exchange_authorization_code(
        self,
        payload: OAuth2TokenRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> OAuth2TokenResponse:
        client = self._client(payload.client_id)
        if payload.scope is not None:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_REQUEST,
                "scope is not accepted for the authorization_code grant.",
            )
        if not payload.code or not payload.redirect_uri or not payload.code_verifier:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_REQUEST,
                "code, redirect_uri and code_verifier are required.",
            )
        if not 32 <= len(payload.code) <= 512:
            raise self._invalid_grant()
        if not _PKCE_VERIFIER.fullmatch(payload.code_verifier):
            raise self._invalid_grant()
        record = await self.db.scalar(
            select(self.authorization_code_model)
            .where(
                self.authorization_code_model.code_hash
                == self.hash_value(payload.code)
            )
            .with_for_update()
        )
        now = aware_utc(self.now())
        expected_challenge = self.pkce_challenge(payload.code_verifier)
        if (
            record is None
            or record.used_at is not None
            or aware_utc(record.expires_at) <= now
            or record.client_id != payload.client_id
            or record.redirect_uri != payload.redirect_uri
            or record.redirect_uri not in client.redirect_uris
            or record.code_challenge_method != "S256"
            or not hmac.compare_digest(record.code_challenge, expected_challenge)
        ):
            raise self._invalid_grant()
        self._scopes(record.scope, client)
        user = await self.users.get_by_id(record.user_id)
        if user is None or not self.users.is_active(user):
            raise self._invalid_grant()
        consumed = await self.db.execute(
            update(self.authorization_code_model)
            .where(
                self.authorization_code_model.id == record.id,
                self.authorization_code_model.used_at.is_(None),
                self.authorization_code_model.expires_at > now,
            )
            .values(used_at=now)
            .execution_options(synchronize_session=False)
        )
        if consumed.rowcount != 1:
            raise self._invalid_grant()
        tokens = await self.sessions.create(
            user,
            ip_address=ip_address,
            user_agent=user_agent,
            oauth_client_id=payload.client_id,
            scope=record.scope,
        )
        return self._token_response(tokens, record.scope)

    async def _exchange_refresh_token(
        self,
        payload: OAuth2TokenRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> OAuth2TokenResponse:
        client = self._client(payload.client_id)
        if not payload.refresh_token:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_REQUEST,
                "refresh_token is required.",
            )
        if payload.code or payload.redirect_uri or payload.code_verifier:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_REQUEST,
                "Authorization code parameters are not accepted for refresh_token.",
            )
        narrowed_scope: str | None = None
        if payload.scope is not None:
            narrowed_scope = " ".join(self._scopes(payload.scope, client))
        try:
            tokens = await self.sessions.rotate(
                payload.refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                oauth_client_id=payload.client_id,
                scope=narrowed_scope,
            )
        except AuthSessionError as exc:
            if exc.code.value == "oauth_scope_invalid":
                raise OAuth2ProtocolError(
                    OAuth2ErrorCode.INVALID_SCOPE,
                    "The requested scope exceeds the originally granted scope.",
                ) from exc
            raise self._invalid_grant() from exc
        access_payload = self.sessions.codec.decode(tokens.access_token, "access")
        return self._token_response(tokens, str(access_payload.get("scope") or ""))

    def _client(self, client_id: str) -> OAuth2ClientConfig:
        client = self.config.oauth2_clients.get(client_id)
        if client is None:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_CLIENT,
                "The client is unknown.",
                status_code=401,
            )
        if not client.enabled:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.UNAUTHORIZED_CLIENT,
                "The client is disabled.",
            )
        if not client.pkce_required:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.UNAUTHORIZED_CLIENT,
                "Public clients must require PKCE S256.",
            )
        if not client.redirect_uris:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.UNAUTHORIZED_CLIENT,
                "The client has no registered redirect URI.",
            )
        try:
            for redirect_uri in client.redirect_uris:
                validate_oauth2_redirect_uri(redirect_uri)
        except ValueError as exc:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.UNAUTHORIZED_CLIENT,
                "The client redirect URI configuration is invalid.",
            ) from exc
        return client

    def _validate_authorization_request(
        self,
        payload: OAuth2AuthorizationRequest,
        client: OAuth2ClientConfig,
    ) -> None:
        if payload.response_type != "code":
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.UNSUPPORTED_RESPONSE_TYPE,
                "Only response_type=code is supported.",
            )
        if payload.redirect_uri not in client.redirect_uris:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_REQUEST,
                "redirect_uri is not registered for this client.",
            )
        try:
            validate_oauth2_redirect_uri(payload.redirect_uri)
        except ValueError as exc:
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_REQUEST,
                "redirect_uri is invalid.",
            ) from exc
        if payload.code_challenge_method != "S256":
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_REQUEST,
                "PKCE code_challenge_method must be S256.",
            )
        if not _PKCE_CHALLENGE.fullmatch(payload.code_challenge):
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_REQUEST,
                "PKCE code_challenge is invalid.",
            )

    @staticmethod
    def _scopes(scope: str, client: OAuth2ClientConfig) -> tuple[str, ...]:
        requested = tuple(dict.fromkeys(scope.split()))
        if any(not _SCOPE_TOKEN.fullmatch(item) for item in requested):
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_SCOPE,
                "The requested scope is malformed.",
            )
        allowed = set(client.scopes)
        if any(item not in allowed for item in requested):
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_SCOPE,
                "The requested scope is not allowed for this client.",
            )
        return requested

    def _token_response(self, tokens: Any, scope: str) -> OAuth2TokenResponse:
        granted_scopes = frozenset(scope.split())
        return OAuth2TokenResponse(
            access_token=tokens.access_token,
            refresh_token=(
                tokens.refresh_token if "offline_access" in granted_scopes else None
            ),
            expires_in=self.config.access_token_minutes * 60,
            scope=scope,
        )

    @staticmethod
    def hash_value(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def pkce_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    @staticmethod
    def _authorization_redirect(
        redirect_uri: str,
        *,
        code: str,
        state: str,
    ) -> str:
        parsed = urlsplit(redirect_uri)
        query = parse_qsl(parsed.query, keep_blank_values=True)
        query.extend((('code', code), ('state', state)))
        return urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), "")
        )

    @staticmethod
    def _invalid_grant() -> OAuth2ProtocolError:
        return OAuth2ProtocolError(
            OAuth2ErrorCode.INVALID_GRANT,
            "The authorization grant is invalid, expired or already used.",
        )
