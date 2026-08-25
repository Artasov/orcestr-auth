from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import Boolean, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from orcestr_auth import AuthConfig, OAuth2ClientConfig
from orcestr_auth.contracts import OAuth2AuthorizationRequest, OAuth2TokenRequest
from orcestr_auth.services.oauth2 import (
    OAuth2AuthorizationService,
    OAuth2ErrorCode,
    OAuth2ProtocolError,
    validate_oauth2_redirect_uri,
)
from orcestr_auth.sqlalchemy import (
    SqlAlchemyUserRepository,
    UserFieldMap,
    create_auth_models,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "oauth2_service_user"
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
CLIENT_ID = "orcestr-real-translate"
OTHER_CLIENT_ID = "other-native-client"
DISABLED_CLIENT_ID = "disabled-native-client"
CALLBACK = "com.orcestr.realtranslate://oauth/callback"
OTHER_CALLBACK = "com.orcestr.realtranslate://oauth/alternate"
VERIFIER = "a" * 64
WRONG_VERIFIER = "b" * 64
STATE = "state-value-with-enough-entropy-1234567890"
NOW = datetime(2026, 8, 25, 10, 0, tzinfo=UTC)


def config() -> AuthConfig:
    return AuthConfig(
        secret_key="oauth2-test-secret",
        oauth2_authorization_code_seconds=120,
        oauth2_clients={
            CLIENT_ID: OAuth2ClientConfig(
                display_name="Orcestr Real Translate",
                redirect_uris=(CALLBACK, OTHER_CALLBACK),
                scopes=("openid", "profile", "email", "offline_access"),
            ),
            OTHER_CLIENT_ID: OAuth2ClientConfig(
                display_name="Other",
                redirect_uris=(CALLBACK,),
                scopes=("openid", "profile", "email", "offline_access"),
            ),
            DISABLED_CLIENT_ID: OAuth2ClientConfig(
                display_name="Disabled",
                redirect_uris=(CALLBACK,),
                scopes=("profile",),
                enabled=False,
            ),
        },
    )


def request(
    *,
    client_id: str = CLIENT_ID,
    redirect_uri: str = CALLBACK,
    verifier: str = VERIFIER,
    scope: str = "openid profile email offline_access",
) -> OAuth2AuthorizationRequest:
    return OAuth2AuthorizationRequest(
        response_type="code",
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=STATE,
        code_challenge=OAuth2AuthorizationService.pkce_challenge(verifier),
        code_challenge_method="S256",
    )


async def setup() -> tuple[object, AsyncSession, User, OAuth2AuthorizationService]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session = AsyncSession(engine, expire_on_commit=False)
    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
        is_active=True,
    )
    session.add(user)
    await session.flush()
    users = SqlAlchemyUserRepository(session, User, FIELDS)
    issued_codes: list[str] = []

    def code_factory() -> str:
        code = f"authorization-code-{len(issued_codes)}-" + "x" * 48
        issued_codes.append(code)
        return code

    service = OAuth2AuthorizationService(
        session,
        models=MODELS,
        users=users,
        config=config(),
        now=lambda: NOW,
        code_factory=code_factory,
    )
    return engine, session, user, service


async def issue(
    service: OAuth2AuthorizationService,
    user: User,
    payload: OAuth2AuthorizationRequest | None = None,
) -> str:
    result = await service.authorize(payload or request(), user)
    query = parse_qs(urlsplit(result.redirect_uri).query)
    assert query["state"] == [STATE]
    return query["code"][0]


def authorization_code_token(
    code: str,
    *,
    client_id: str = CLIENT_ID,
    redirect_uri: str = CALLBACK,
    verifier: str = VERIFIER,
) -> OAuth2TokenRequest:
    return OAuth2TokenRequest(
        grant_type="authorization_code",
        client_id=client_id,
        code=code,
        redirect_uri=redirect_uri,
        code_verifier=verifier,
    )


def test_context_requires_registered_exact_redirect_and_s256() -> None:
    payload = request()
    service_config = config()
    assert service_config.oauth2_clients[CLIENT_ID].display_name == (
        "Orcestr Real Translate"
    )

    # context() performs no I/O, so a minimally constructed instance is enough.
    service = object.__new__(OAuth2AuthorizationService)
    service.config = service_config
    context = service.context(payload)
    assert context.requested_scopes == (
        "openid",
        "profile",
        "email",
        "offline_access",
    )
    assert context.redirect_uri == CALLBACK

    for rejected in (
        payload.model_copy(update={"redirect_uri": CALLBACK.upper()}),
        payload.model_copy(update={"redirect_uri": f"{CALLBACK}?next=1"}),
        payload.model_copy(update={"code_challenge_method": "plain"}),
        payload.model_copy(update={"code_challenge": "short"}),
    ):
        with pytest.raises(OAuth2ProtocolError):
            service.context(rejected)

    with pytest.raises(OAuth2ProtocolError) as unknown:
        service.context(payload.model_copy(update={"client_id": "unknown"}))
    assert unknown.value.error == OAuth2ErrorCode.INVALID_CLIENT
    assert unknown.value.status_code == 401

    with pytest.raises(OAuth2ProtocolError) as disabled:
        service.context(payload.model_copy(update={"client_id": DISABLED_CLIENT_ID}))
    assert disabled.value.error == OAuth2ErrorCode.UNAUTHORIZED_CLIENT

    with pytest.raises(OAuth2ProtocolError) as scope:
        service.context(payload.model_copy(update={"scope": "admin"}))
    assert scope.value.error == OAuth2ErrorCode.INVALID_SCOPE


async def test_authorization_code_is_hashed_bound_and_one_time() -> None:
    engine, session, user, service = await setup()
    try:
        code = await issue(service, user)
        record = await session.scalar(select(MODELS.authorization_code))
        assert record is not None
        assert record.code_hash == service.hash_value(code)
        assert record.state_hash == service.hash_value(STATE)
        assert code not in record.code_hash
        assert STATE not in record.state_hash
        assert record.client_id == CLIENT_ID
        assert record.redirect_uri == CALLBACK
        assert record.scope == "openid profile email offline_access"
        assert record.expires_at.replace(tzinfo=UTC) == NOW + timedelta(seconds=120)

        response = await service.token(
            authorization_code_token(code),
            ip_address="127.0.0.1",
            user_agent="test-client",
        )
        assert response.token_type == "Bearer"
        assert response.scope == "openid profile email offline_access"
        assert response.refresh_token
        assert response.expires_in == 900
        claims = service.sessions.codec.decode(response.access_token, "access")
        assert claims["client_id"] == CLIENT_ID
        assert claims["scope"] == "openid profile email offline_access"
        auth_session = await session.get(MODELS.session, claims["sid"])
        assert auth_session.oauth_client_id == CLIENT_ID
        assert auth_session.scope == "openid profile email offline_access"

        with pytest.raises(OAuth2ProtocolError) as replay:
            await service.token(authorization_code_token(code))
        assert replay.value.error == OAuth2ErrorCode.INVALID_GRANT
    finally:
        await session.close()
        await engine.dispose()


@pytest.mark.parametrize(
    ("client_id", "redirect_uri", "verifier"),
    [
        (CLIENT_ID, CALLBACK, WRONG_VERIFIER),
        (OTHER_CLIENT_ID, CALLBACK, VERIFIER),
        (CLIENT_ID, OTHER_CALLBACK, VERIFIER),
    ],
)
async def test_failed_exchange_does_not_consume_valid_code(
    client_id: str,
    redirect_uri: str,
    verifier: str,
) -> None:
    engine, session, user, service = await setup()
    try:
        code = await issue(service, user)
        with pytest.raises(OAuth2ProtocolError) as rejected:
            await service.token(
                authorization_code_token(
                    code,
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    verifier=verifier,
                )
            )
        assert rejected.value.error == OAuth2ErrorCode.INVALID_GRANT
        record = await session.scalar(select(MODELS.authorization_code))
        assert record.used_at is None
        accepted = await service.token(authorization_code_token(code))
        assert accepted.access_token
    finally:
        await session.close()
        await engine.dispose()


async def test_expired_code_is_rejected_without_creating_session() -> None:
    engine, session, user, service = await setup()
    try:
        code = await issue(service, user)
        service.now = lambda: NOW + timedelta(minutes=3)
        service.sessions.now = service.now
        with pytest.raises(OAuth2ProtocolError) as rejected:
            await service.token(authorization_code_token(code))
        assert rejected.value.error == OAuth2ErrorCode.INVALID_GRANT
        assert await session.scalar(select(MODELS.session)) is None
    finally:
        await session.close()
        await engine.dispose()


async def test_refresh_is_client_bound_rotated_and_scope_can_only_narrow() -> None:
    engine, session, user, service = await setup()
    try:
        code = await issue(service, user)
        first = await service.token(authorization_code_token(code))

        with pytest.raises(OAuth2ProtocolError) as wrong_client:
            await service.token(
                OAuth2TokenRequest(
                    grant_type="refresh_token",
                    client_id=OTHER_CLIENT_ID,
                    refresh_token=first.refresh_token,
                )
            )
        assert wrong_client.value.error == OAuth2ErrorCode.INVALID_GRANT

        second = await service.token(
            OAuth2TokenRequest(
                grant_type="refresh_token",
                client_id=CLIENT_ID,
                refresh_token=first.refresh_token,
                scope="profile offline_access",
            )
        )
        assert second.refresh_token != first.refresh_token
        assert second.scope == "profile offline_access"

        with pytest.raises(OAuth2ProtocolError) as expanded:
            await service.token(
                OAuth2TokenRequest(
                    grant_type="refresh_token",
                    client_id=CLIENT_ID,
                    refresh_token=second.refresh_token,
                    scope="profile email offline_access",
                )
            )
        assert expanded.value.error == OAuth2ErrorCode.INVALID_SCOPE

        third = await service.token(
            OAuth2TokenRequest(
                grant_type="refresh_token",
                client_id=CLIENT_ID,
                refresh_token=second.refresh_token,
            )
        )
        assert third.scope == "profile offline_access"
    finally:
        await session.close()
        await engine.dispose()


async def test_revoke_cannot_cross_client_boundary() -> None:
    engine, session, user, service = await setup()
    try:
        code = await issue(service, user)
        tokens = await service.token(authorization_code_token(code))
        assert not await service.revoke(
            client_id=OTHER_CLIENT_ID,
            token=tokens.refresh_token,
        )
        rotated = await service.token(
            OAuth2TokenRequest(
                grant_type="refresh_token",
                client_id=CLIENT_ID,
                refresh_token=tokens.refresh_token,
            )
        )
        assert await service.revoke(
            client_id=CLIENT_ID,
            token=rotated.refresh_token,
        )
        with pytest.raises(OAuth2ProtocolError) as revoked:
            await service.token(
                OAuth2TokenRequest(
                    grant_type="refresh_token",
                    client_id=CLIENT_ID,
                    refresh_token=rotated.refresh_token,
                )
            )
        assert revoked.value.error == OAuth2ErrorCode.INVALID_GRANT
    finally:
        await session.close()
        await engine.dispose()


async def test_refresh_token_is_only_returned_for_offline_access() -> None:
    engine, session, user, service = await setup()
    try:
        code = await issue(service, user, request(scope="openid profile"))
        online = await service.token(authorization_code_token(code))
        assert online.refresh_token is None

        offline_code = await issue(service, user)
        offline = await service.token(authorization_code_token(offline_code))
        assert offline.refresh_token
        narrowed = await service.token(
            OAuth2TokenRequest(
                grant_type="refresh_token",
                client_id=CLIENT_ID,
                refresh_token=offline.refresh_token,
                scope="profile",
            )
        )
        assert narrowed.scope == "profile"
        assert narrowed.refresh_token is None
    finally:
        await session.close()
        await engine.dispose()


@pytest.mark.parametrize(
    "redirect_uri",
    [
        "https://client.example/oauth/callback",
        "http://localhost:43119/oauth/callback",
        "http://127.0.0.9:43119/oauth/callback",
        "http://[::1]:43119/oauth/callback",
        "com.orcestr.realtranslate://oauth/callback",
        "com.orcestr.realtranslate:/oauth/callback",
    ],
)
def test_redirect_validator_accepts_safe_public_client_uris(
    redirect_uri: str,
) -> None:
    validate_oauth2_redirect_uri(redirect_uri)


@pytest.mark.parametrize(
    "redirect_uri",
    [
        "http://client.example/oauth/callback",
        "javascript:alert(1)",
        "data:text/plain,callback",
        "file:///tmp/callback",
        "blob:https://client.example/id",
        "about:blank",
        "vbscript:msgbox(1)",
        "https://user:password@client.example/callback",
        "https://client.example/callback#fragment",
        "https://client.example:invalid/callback",
        "https://client.example/%ZZ",
        "https://client.example/%0Acallback",
        "https://client.example\\@attacker.example/callback",
        "myapp://oauth/callback",
        "com.orcestr://oauth/callback",
        "com.orcestr.realtranslate://oauth:123/callback",
        "com.orcestr.realtranslate:callback",
    ],
)
def test_redirect_validator_rejects_unsafe_or_malformed_uris(
    redirect_uri: str,
) -> None:
    with pytest.raises(ValueError):
        validate_oauth2_redirect_uri(redirect_uri)
