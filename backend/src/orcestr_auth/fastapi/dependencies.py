from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import AuthConfig
from ..sqlalchemy import AuthModelSet, SqlAlchemyUserRepository, UserFieldMap
from ..tokens import TokenCodec, TokenPayloadError

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass(frozen=True, slots=True)
class AuthDependencies:
    current_user: Callable[..., Any]
    current_user_or_none: Callable[..., Any]
    require_cookie_csrf: Callable[[Request], None]


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
        if credentials is None and token:
            _require_cookie_csrf(request)
        if not token:
            if required:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not_authenticated")
            return None
        try:
            payload = codec.decode(token, "access")
        except TokenPayloadError as exc:
            if required:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
            return None
        user_id = _coerce_id(payload["sub"], user_fields.id.property.columns[0].type)
        session_id = payload.get("sid")
        if session_id:
            auth_session = await session.get(models.session, str(session_id))
            if (
                auth_session is None
                or auth_session.user_id != user_id
                or auth_session.revoked_at is not None
                or _aware(auth_session.expires_at) <= datetime.now(UTC)
            ):
                if required:
                    raise HTTPException(
                        status.HTTP_401_UNAUTHORIZED, "session_expired"
                    )
                return None
        users = SqlAlchemyUserRepository(session, user_model, user_fields)
        user = await users.get_by_id(user_id)
        if user is None or not users.is_active(user):
            if required:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user_not_found")
            return None
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

    return AuthDependencies(current_user, current_user_or_none, require_cookie_csrf)


def _require_cookie_csrf(request: Request) -> None:
    if request.method.upper() not in MUTATING_METHODS:
        return
    if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "csrf_header_missing")


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _coerce_id(value: str, column_type: Any) -> Any:
    python_type = getattr(column_type, "python_type", str)
    try:
        return python_type(value)
    except (TypeError, ValueError) as exc:
        raise TokenPayloadError("Invalid subject.") from exc
