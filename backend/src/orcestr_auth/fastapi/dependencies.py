from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import AuthConfig
from ..errors import AuthErrorCode, auth_api_error
from ..sqlalchemy import AuthModelSet, SqlAlchemyUserRepository, UserFieldMap
from ..tokens import TokenCodec, TokenPayloadError

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_SCOPE_TOKEN = re.compile(r'^[\x21\x23-\x5B\x5D-\x7E]+$')
_INVALID_BEARER = {'WWW-Authenticate': 'Bearer error="invalid_token"'}


@dataclass(frozen=True, slots=True)
class OAuth2Principal:
    """A user authenticated by a registered OAuth 2 public client."""

    user: Any
    client_id: str
    session_id: str
    scopes: frozenset[str]


@dataclass(frozen=True, slots=True)
class AuthDependencies:
    current_user: Callable[..., Any]
    current_user_or_none: Callable[..., Any]
    require_cookie_csrf: Callable[[Request], None]
    require_oauth2_scopes: Callable[..., Callable[..., Any]]


def create_auth_dependencies(
    *,
    config: AuthConfig,
    session_dependency: Callable[..., Any],
    user_model: type[Any],
    user_fields: UserFieldMap,
    models: AuthModelSet,
) -> AuthDependencies:
    bearer = HTTPBearer(auto_error=False)
    codec = TokenCodec(config)

    def require_cookie_csrf(request: Request) -> None:
        if request.cookies.get(config.cookie.access_name) or request.cookies.get(
            config.cookie.refresh_name
        ):
            _require_cookie_csrf(request)

    async def resolve(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None,
        session: AsyncSession,
        *,
        required: bool,
    ) -> Any | None:
        token = (
            credentials.credentials
            if credentials is not None
            else request.cookies.get(config.cookie.access_name)
        )
        refresh_cookie = request.cookies.get(config.cookie.refresh_name)
        if credentials is None and token:
            _require_cookie_csrf(request)
        if not token:
            if required or refresh_cookie:
                raise auth_api_error(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=(
                        AuthErrorCode.SESSION_EXPIRED
                        if refresh_cookie
                        else AuthErrorCode.NOT_AUTHENTICATED
                    ),
                )
            return None
        try:
            payload = codec.decode(token, "access")
            user_id = _coerce_id(
                payload["sub"],
                user_fields.id.property.columns[0].type,
            )
        except (KeyError, TokenPayloadError) as exc:
            raise auth_api_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=AuthErrorCode.SESSION_INVALID,
            ) from exc
        session_id = payload.get("sid")
        auth_session: Any | None = None
        if session_id:
            auth_session = await session.get(models.session, str(session_id))
            if (
                auth_session is None
                or auth_session.user_id != user_id
                or auth_session.revoked_at is not None
                or _aware(auth_session.expires_at) <= datetime.now(UTC)
            ):
                raise auth_api_error(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=AuthErrorCode.SESSION_EXPIRED,
                )
        _reject_oauth2_token_on_default_dependency(payload, auth_session)
        users = SqlAlchemyUserRepository(session, user_model, user_fields)
        user = await users.get_by_id(user_id)
        if user is None or not users.is_active(user):
            raise auth_api_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=AuthErrorCode.SESSION_INVALID,
            )
        return user

    async def current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        session: AsyncSession = Depends(session_dependency),
    ) -> Any:
        return await resolve(request, credentials, session, required=True)

    async def current_user_or_none(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        session: AsyncSession = Depends(session_dependency),
    ) -> Any | None:
        return await resolve(request, credentials, session, required=False)

    def require_oauth2_scopes(*required: str) -> Callable[..., Any]:
        required_scopes = _required_scopes(required)

        async def oauth2_principal(
            credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
            session: AsyncSession = Depends(session_dependency),
        ) -> OAuth2Principal:
            if credentials is None or credentials.scheme.lower() != "bearer":
                raise auth_api_error(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=AuthErrorCode.OAUTH2_CLIENT_TOKEN_REQUIRED,
                    headers={"WWW-Authenticate": "Bearer"},
                )
            try:
                payload = codec.decode(credentials.credentials, "access")
                user_id = _coerce_id(
                    payload["sub"],
                    user_fields.id.property.columns[0].type,
                )
            except (KeyError, TokenPayloadError) as exc:
                raise _oauth2_invalid_token() from exc

            session_id = payload.get("sid")
            client_id = payload.get("client_id")
            scope_claim = payload.get("scope")
            if (
                not isinstance(session_id, str)
                or not session_id
                or not isinstance(client_id, str)
                or not client_id
                or not isinstance(scope_claim, str)
            ):
                raise _oauth2_invalid_token()

            client = config.oauth2_clients.get(client_id)
            if client is None or not client.enabled or not client.pkce_required:
                raise _oauth2_invalid_token()

            auth_session = await session.get(models.session, session_id)
            if (
                auth_session is None
                or auth_session.user_id != user_id
                or auth_session.revoked_at is not None
                or _aware(auth_session.expires_at) <= datetime.now(UTC)
                or auth_session.oauth_client_id != client_id
                or not isinstance(auth_session.scope, str)
            ):
                raise _oauth2_invalid_token()

            try:
                token_scopes = _scope_set(scope_claim)
                session_scopes = _scope_set(auth_session.scope)
                registered_scopes = _configured_scope_set(client.scopes)
            except ValueError as exc:
                raise _oauth2_invalid_token() from exc
            if not token_scopes.issubset(session_scopes) or not (
                session_scopes.issubset(registered_scopes)
            ):
                raise _oauth2_invalid_token()
            if not required_scopes.issubset(token_scopes):
                challenge = 'Bearer error="insufficient_scope"'
                if required_scopes:
                    challenge += f', scope="{" ".join(sorted(required_scopes))}"'
                raise auth_api_error(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code=AuthErrorCode.OAUTH2_INSUFFICIENT_SCOPE,
                    headers={"WWW-Authenticate": challenge},
                )

            users = SqlAlchemyUserRepository(session, user_model, user_fields)
            user = await users.get_by_id(user_id)
            if user is None or not users.is_active(user):
                raise _oauth2_invalid_token()
            return OAuth2Principal(
                user=user,
                client_id=client_id,
                session_id=session_id,
                scopes=token_scopes,
            )

        return oauth2_principal

    return AuthDependencies(
        current_user,
        current_user_or_none,
        require_cookie_csrf,
        require_oauth2_scopes,
    )


def _reject_oauth2_token_on_default_dependency(
    payload: dict[str, Any],
    auth_session: Any | None,
) -> None:
    claim_client = payload.get("client_id")
    has_scope_claim = "scope" in payload
    session_client = getattr(auth_session, "oauth_client_id", None)
    session_scope = getattr(auth_session, "scope", None)
    has_oauth2_metadata = (
        claim_client is not None
        or has_scope_claim
        or session_client is not None
        or session_scope is not None
    )
    if not has_oauth2_metadata:
        return
    if (
        auth_session is None
        or not isinstance(claim_client, str)
        or not claim_client
        or not isinstance(payload.get("scope"), str)
        or session_client != claim_client
        or not isinstance(session_scope, str)
    ):
        raise _oauth2_invalid_token()
    raise auth_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code=AuthErrorCode.OAUTH2_CLIENT_TOKEN_NOT_ALLOWED,
    )


def _oauth2_invalid_token() -> Any:
    return auth_api_error(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=AuthErrorCode.OAUTH2_CLIENT_TOKEN_INVALID,
        headers=_INVALID_BEARER,
    )


def _required_scopes(scopes: tuple[str, ...]) -> frozenset[str]:
    if any(not isinstance(item, str) or not _SCOPE_TOKEN.fullmatch(item) for item in scopes):
        raise ValueError("Required OAuth2 scopes must be valid single scope tokens.")
    return frozenset(scopes)


def _scope_set(scope: str) -> frozenset[str]:
    if len(scope) > 1024:
        raise ValueError("OAuth2 scope is too long.")
    tokens = scope.split()
    if any(not _SCOPE_TOKEN.fullmatch(item) for item in tokens):
        raise ValueError("OAuth2 scope is malformed.")
    return frozenset(tokens)


def _configured_scope_set(scopes: tuple[str, ...]) -> frozenset[str]:
    if any(not _SCOPE_TOKEN.fullmatch(item) for item in scopes):
        raise ValueError("Configured OAuth2 scope is malformed.")
    return frozenset(scopes)


def _require_cookie_csrf(request: Request) -> None:
    if request.method.upper() not in MUTATING_METHODS:
        return
    if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
        return
    raise auth_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code=AuthErrorCode.CSRF_HEADER_MISSING,
    )


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _coerce_id(value: str, column_type: Any) -> Any:
    python_type = getattr(column_type, "python_type", str)
    try:
        return python_type(value)
    except (TypeError, ValueError) as exc:
        raise TokenPayloadError("Invalid subject.") from exc
