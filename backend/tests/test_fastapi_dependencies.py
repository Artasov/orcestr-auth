from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from orcestr_auth import AuthConfig, OAuth2ClientConfig, TokenCodec
from orcestr_auth.fastapi import OAuth2Principal, create_auth_dependencies
from orcestr_auth.sqlalchemy import UserFieldMap, create_auth_models
from orcestr_core import ApiError


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "dependency_test_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


FIELDS = UserFieldMap(
    id=User.id,
    username=User.username,
    email=User.email,
    password_hash=User.password_hash,
    is_active=User.is_active,
)
MODELS = create_auth_models(registry=Base.registry, user_model=User)
NATIVE_CLIENT_ID = "native-client"
DISABLED_CLIENT_ID = "disabled-client"
CONFIG = AuthConfig(
    secret_key="test-secret",
    oauth2_clients={
        NATIVE_CLIENT_ID: OAuth2ClientConfig(
            display_name="Native client",
            redirect_uris=("com.orcestr.nativeclient://oauth/callback",),
            scopes=("openid", "profile", "email", "offline_access"),
        ),
        DISABLED_CLIENT_ID: OAuth2ClientConfig(
            display_name="Disabled client",
            redirect_uris=("com.orcestr.disabledclient://oauth/callback",),
            scopes=("openid",),
            enabled=False,
        ),
    },
)


async def _unused_session_dependency() -> None:
    return None


DEPENDENCIES = create_auth_dependencies(
    config=CONFIG,
    session_dependency=_unused_session_dependency,
    user_model=User,
    user_fields=FIELDS,
    models=MODELS,
)


def _request(*, cookie: str | None = None) -> Request:
    headers = [] if cookie is None else [(b"cookie", cookie.encode("ascii"))]
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "https",
            "path": "/optional",
            "raw_path": b"/optional",
            "query_string": b"",
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 443),
        }
    )


class _UnusedSession:
    async def get(self, model: type[Any], key: Any) -> None:
        return None


class _ExpiredSessionStore:
    async def get(self, model: type[Any], key: Any) -> Any:
        return model(
            id=str(key),
            user_id=1,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
            last_used_at=datetime.now(UTC) - timedelta(minutes=2),
        )


async def test_optional_auth_allows_a_truly_anonymous_request() -> None:
    user = await DEPENDENCIES.current_user_or_none(
        _request(),
        None,
        _UnusedSession(),
    )

    assert user is None


async def test_optional_auth_rejects_refresh_only_browser_session() -> None:
    with pytest.raises(ApiError) as captured:
        await DEPENDENCIES.current_user_or_none(
            _request(cookie=f"{CONFIG.cookie.refresh_name}=refresh-token"),
            None,
            _UnusedSession(),
        )

    assert captured.value.status_code == 401
    assert captured.value.code == "session_expired"


async def test_optional_auth_rejects_invalid_access_token() -> None:
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="not-a-token",
    )

    with pytest.raises(ApiError) as captured:
        await DEPENDENCIES.current_user_or_none(
            _request(),
            credentials,
            _UnusedSession(),
        )

    assert captured.value.status_code == 401
    assert captured.value.code == "session_invalid"


async def test_optional_auth_rejects_invalid_access_cookie() -> None:
    with pytest.raises(ApiError) as captured:
        await DEPENDENCIES.current_user_or_none(
            _request(cookie=f"{CONFIG.cookie.access_name}=not-a-token"),
            None,
            _UnusedSession(),
        )

    assert captured.value.status_code == 401
    assert captured.value.code == "session_invalid"


async def test_optional_auth_rejects_non_coercible_subject() -> None:
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=TokenCodec(CONFIG).create_access_token("not-an-integer"),
    )

    with pytest.raises(ApiError) as captured:
        await DEPENDENCIES.current_user_or_none(
            _request(),
            credentials,
            _UnusedSession(),
        )

    assert captured.value.status_code == 401
    assert captured.value.code == "session_invalid"


async def test_optional_auth_rejects_expired_auth_session() -> None:
    access_token = TokenCodec(CONFIG).create_access_token(1, session_id="expired")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token,
    )

    with pytest.raises(ApiError) as captured:
        await DEPENDENCIES.current_user_or_none(
            _request(),
            credentials,
            _ExpiredSessionStore(),
        )

    assert captured.value.status_code == 401
    assert captured.value.code == "session_expired"


async def test_optional_auth_resolves_a_valid_user() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        expected = User(
            id=1,
            username="user",
            email="user@example.com",
            password_hash="hash",
            is_active=True,
        )
        session.add(expected)
        await session.commit()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=TokenCodec(CONFIG).create_access_token(expected.id),
        )

        actual = await DEPENDENCIES.current_user_or_none(
            _request(),
            credentials,
            session,
        )

        assert actual.id == expected.id

    await engine.dispose()


async def test_default_dependency_rejects_client_bound_token_and_scope_guard_accepts_it() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        expected = User(
            id=11,
            username="oauth-user",
            email="oauth-user@example.com",
            password_hash="hash",
            is_active=True,
        )
        session.add(expected)
        session.add(
            MODELS.session(
                id="oauth-session",
                user_id=expected.id,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                last_used_at=datetime.now(UTC),
                oauth_client_id=NATIVE_CLIENT_ID,
                scope="openid profile",
            )
        )
        await session.commit()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=TokenCodec(CONFIG).create_access_token(
                expected.id,
                session_id="oauth-session",
                client_id=NATIVE_CLIENT_ID,
                scope="openid profile",
            ),
        )

        with pytest.raises(ApiError) as default_rejected:
            await DEPENDENCIES.current_user(_request(), credentials, session)
        assert default_rejected.value.status_code == 403
        assert default_rejected.value.code == "oauth2_client_token_not_allowed"

        dependency = DEPENDENCIES.require_oauth2_scopes("openid", "profile")
        principal = await dependency(credentials, session)
        assert isinstance(principal, OAuth2Principal)
        assert principal.user.id == expected.id
        assert principal.client_id == NATIVE_CLIENT_ID
        assert principal.session_id == "oauth-session"
        assert principal.scopes == frozenset({"openid", "profile"})

        with pytest.raises(ApiError) as insufficient:
            await DEPENDENCIES.require_oauth2_scopes("email")(
                credentials,
                session,
            )
        assert insufficient.value.status_code == 403
        assert insufficient.value.code == "oauth2_insufficient_scope"
        assert "insufficient_scope" in insufficient.value.headers["WWW-Authenticate"]

    await engine.dispose()


async def test_scope_guard_is_bearer_only_and_rejects_invalid_client_binding() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        user = User(
            id=12,
            username="guard-user",
            email="guard-user@example.com",
            password_hash="hash",
            is_active=True,
        )
        session.add(user)
        session.add_all(
            [
                MODELS.session(
                    id="mismatched-scope-session",
                    user_id=user.id,
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                    last_used_at=datetime.now(UTC),
                    oauth_client_id=NATIVE_CLIENT_ID,
                    scope="openid",
                ),
                MODELS.session(
                    id="disabled-client-session",
                    user_id=user.id,
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                    last_used_at=datetime.now(UTC),
                    oauth_client_id=DISABLED_CLIENT_ID,
                    scope="openid",
                ),
            ]
        )
        await session.commit()
        dependency = DEPENDENCIES.require_oauth2_scopes("openid")

        with pytest.raises(ApiError) as missing:
            await dependency(None, session)
        assert missing.value.status_code == 401
        assert missing.value.code == "oauth2_client_token_required"

        basic = HTTPAuthorizationCredentials(scheme="Basic", credentials="secret")
        with pytest.raises(ApiError) as non_bearer:
            await dependency(basic, session)
        assert non_bearer.value.code == "oauth2_client_token_required"

        mismatched_scope = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=TokenCodec(CONFIG).create_access_token(
                user.id,
                session_id="mismatched-scope-session",
                client_id=NATIVE_CLIENT_ID,
                scope="openid profile",
            ),
        )
        with pytest.raises(ApiError) as invalid_scope_binding:
            await dependency(mismatched_scope, session)
        assert invalid_scope_binding.value.status_code == 401
        assert invalid_scope_binding.value.code == "oauth2_client_token_invalid"

        disabled = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=TokenCodec(CONFIG).create_access_token(
                user.id,
                session_id="disabled-client-session",
                client_id=DISABLED_CLIENT_ID,
                scope="openid",
            ),
        )
        with pytest.raises(ApiError) as disabled_client:
            await dependency(disabled, session)
        assert disabled_client.value.code == "oauth2_client_token_invalid"

    await engine.dispose()
