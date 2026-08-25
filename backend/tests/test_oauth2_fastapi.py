from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from orcestr_auth import AuthConfig, CookieConfig
from orcestr_auth.contracts import (
    OAuth2AuthorizationContext,
    OAuth2AuthorizationRequest,
    OAuth2AuthorizationResponse,
    OAuth2TokenRequest,
    OAuth2TokenResponse,
)
from orcestr_auth.fastapi import OAuth2Principal, create_oauth2_router
from orcestr_auth.services import OAuth2ErrorCode, OAuth2ProtocolError

CLIENT_ID = "orcestr-real-translate"
CALLBACK = "com.orcestr.realtranslate://oauth/callback"
STATE = "state-value-with-enough-entropy-1234567890"
CHALLENGE = "a" * 43


class UserInfoResponse(BaseModel):
    sub: str
    name: str | None = None


class FakeOAuth2Application:
    def __init__(self) -> None:
        self.tokens: list[OAuth2TokenRequest] = []
        self.revocations: list[tuple[str, str]] = []
        self.userinfo_principals: list[OAuth2Principal] = []

    def context(
        self,
        payload: OAuth2AuthorizationRequest,
    ) -> OAuth2AuthorizationContext:
        return OAuth2AuthorizationContext(
            client_id=payload.client_id,
            display_name="Orcestr Real Translate",
            redirect_uri=payload.redirect_uri,
            requested_scopes=tuple(payload.scope.split()),
            state=payload.state,
            code_challenge=payload.code_challenge,
        )

    async def authorize(
        self,
        payload: OAuth2AuthorizationRequest,
        user: Any,
    ) -> OAuth2AuthorizationResponse:
        return OAuth2AuthorizationResponse(
            redirect_uri=f"{payload.redirect_uri}?code=one-time-code&state={payload.state}"
        )

    async def token(
        self,
        payload: OAuth2TokenRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> OAuth2TokenResponse:
        self.tokens.append(payload)
        if payload.code == "rejected-code":
            raise OAuth2ProtocolError(
                OAuth2ErrorCode.INVALID_GRANT,
                "The authorization grant is invalid.",
            )
        return OAuth2TokenResponse(
            access_token="access",
            refresh_token=(None if payload.code == "online-code" else "refresh"),
            expires_in=900,
            scope="profile",
        )

    async def revoke(self, *, client_id: str, token: str) -> bool:
        self.revocations.append((client_id, token))
        return True

    async def userinfo(self, principal: OAuth2Principal) -> UserInfoResponse:
        self.userinfo_principals.append(principal)
        return UserInfoResponse(sub=str(principal.user["id"]), name="Test User")


def build_app() -> tuple[FastAPI, FakeOAuth2Application]:
    application = FakeOAuth2Application()
    config = AuthConfig(
        secret_key="test-secret",
        cookie=CookieConfig(secure=False),
    )

    async def get_application() -> FakeOAuth2Application:
        return application

    async def get_current_user() -> dict[str, Any]:
        return {"id": 1}

    async def get_oauth2_principal() -> OAuth2Principal:
        return OAuth2Principal(
            user={"id": 1},
            client_id=CLIENT_ID,
            session_id="session-id",
            scopes=frozenset({"openid", "profile"}),
        )

    app = FastAPI()
    app.include_router(
        create_oauth2_router(
            config=config,
            application_dependency=get_application,
            current_user_dependency=get_current_user,
            oauth2_principal_dependency=get_oauth2_principal,
            userinfo_response_model=UserInfoResponse,
        ),
        prefix="/api/v1/auth/oauth2",
    )
    return app, application


def authorization_payload() -> dict[str, str]:
    return {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": CALLBACK,
        "scope": "profile",
        "state": STATE,
        "code_challenge": CHALLENGE,
        "code_challenge_method": "S256",
    }


async def test_context_and_authorize_wire_contract_and_csrf() -> None:
    app, _ = build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        context = await client.get(
            "/api/v1/auth/oauth2/authorize/",
            params=authorization_payload(),
        )
        assert context.status_code == 200
        assert context.json()["display_name"] == "Orcestr Real Translate"
        assert context.json()["requested_scopes"] == ["profile"]
        assert context.headers["cache-control"] == "no-store"
        assert context.headers["pragma"] == "no-cache"

        client.cookies.set("orcestr_access", "browser-token")
        rejected = await client.post(
            "/api/v1/auth/oauth2/authorize/",
            json=authorization_payload(),
        )
        assert rejected.status_code == 403
        assert rejected.json()["error"] == "access_denied"
        assert rejected.headers["cache-control"] == "no-store"

        accepted = await client.post(
            "/api/v1/auth/oauth2/authorize/",
            json=authorization_payload(),
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        assert accepted.status_code == 200
        redirect_uri = accepted.json()["redirect_uri"]
        assert "code=one-time-code" in redirect_uri
        assert f"state={STATE}" in redirect_uri
        assert "access" not in redirect_uri
        assert "refresh" not in redirect_uri


async def test_token_accepts_form_returns_standard_no_store_response() -> None:
    app, application = build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/auth/oauth2/token/",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "code": "authorization-code-value",
                "redirect_uri": CALLBACK,
                "code_verifier": "v" * 64,
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "access_token": "access",
            "refresh_token": "refresh",
            "token_type": "Bearer",
            "expires_in": 900,
            "scope": "profile",
        }
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["pragma"] == "no-cache"
        assert application.tokens[0].grant_type == "authorization_code"

        online = await client.post(
            "/api/v1/auth/oauth2/token/",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "code": "online-code",
                "redirect_uri": CALLBACK,
                "code_verifier": "v" * 64,
            },
        )
        assert online.status_code == 200
        assert "refresh_token" not in online.json()

        refreshed = await client.post(
            "/api/v1/auth/oauth2/token/",
            json={
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "refresh_token": "refresh",
            },
        )
        assert refreshed.status_code == 200
        assert application.tokens[2].refresh_token == "refresh"

        secret_rejected = await client.post(
            "/api/v1/auth/oauth2/token/",
            json={
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "client_secret": "public-clients-have-no-secret",
                "refresh_token": "refresh",
            },
        )
        assert secret_rejected.status_code == 400
        assert secret_rejected.json()["error"] == "invalid_request"

        schema = (await client.get("/openapi.json")).json()
        token_body = schema["paths"]["/api/v1/auth/oauth2/token/"]["post"][
            "requestBody"
        ]["content"]
        assert "application/json" in token_body
        assert "application/x-www-form-urlencoded" in token_body
        authorize_parameters = schema["paths"][
            "/api/v1/auth/oauth2/authorize/"
        ]["get"]["parameters"]
        assert {item["name"] for item in authorize_parameters} >= {
            "client_id",
            "redirect_uri",
            "state",
            "code_challenge",
        }


async def test_token_errors_and_revocation_use_oauth_json() -> None:
    app, application = build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        malformed = await client.post(
            "/api/v1/auth/oauth2/token/",
            content=(
                "grant_type=authorization_code&client_id=first&client_id=second"
            ),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert malformed.status_code == 400
        assert malformed.json()["error"] == "invalid_request"

        invalid_grant = await client.post(
            "/api/v1/auth/oauth2/token/",
            json={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "code": "rejected-code",
                "redirect_uri": CALLBACK,
                "code_verifier": "v" * 64,
            },
        )
        assert invalid_grant.status_code == 400
        assert invalid_grant.json() == {
            "error": "invalid_grant",
            "error_description": "The authorization grant is invalid.",
        }
        assert invalid_grant.headers["cache-control"] == "no-store"

        revoked = await client.post(
            "/api/v1/auth/oauth2/revoke/",
            data={
                "client_id": CLIENT_ID,
                "token": "refresh",
                "token_type_hint": "refresh_token",
            },
        )
        assert revoked.status_code == 200
        assert revoked.content == b""
        assert revoked.headers["cache-control"] == "no-store"
        assert application.revocations == [(CLIENT_ID, "refresh")]


async def test_userinfo_hook_is_scope_dependency_driven_and_never_cached() -> None:
    app, application = build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/auth/oauth2/userinfo/")

    assert response.status_code == 200
    assert response.json() == {"sub": "1", "name": "Test User"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    assert application.userinfo_principals[0].client_id == CLIENT_ID
    assert application.userinfo_principals[0].scopes == frozenset(
        {"openid", "profile"}
    )
