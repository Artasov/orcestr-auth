from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from orcestr_auth.config import AuthConfig, CookieConfig
from orcestr_auth.contracts import AuthTokens, LoginInput, OAuthCallbackInput
from orcestr_auth.fastapi import AuthResult, create_auth_router


class UserResponse(BaseModel):
    id: int
    username: str


class RegisterPayload(BaseModel):
    username: str
    password: str


class FakeAuthApplication:
    def __init__(self) -> None:
        self.refresh_tokens: list[str | None] = []
        self.logout_tokens: list[tuple[str | None, str | None]] = []

    @staticmethod
    def _result(username: str = "admin") -> AuthResult:
        return AuthResult(
            user={"id": 1, "username": username},
            tokens=AuthTokens(access_token="access", refresh_token="refresh"),
        )

    async def register(self, payload: BaseModel, request: Request) -> AuthResult:
        return self._result(str(getattr(payload, "username")))

    async def login(self, payload: LoginInput, request: Request) -> AuthResult:
        return self._result(payload.username)

    async def oauth(
        self, provider: str, payload: OAuthCallbackInput, request: Request
    ) -> AuthResult:
        return self._result(provider)

    async def refresh(
        self, refresh_token: str | None, request: Request
    ) -> AuthTokens:
        self.refresh_tokens.append(refresh_token)
        return AuthTokens(access_token="next-access", refresh_token="next-refresh")

    async def logout(
        self,
        *,
        access_token: str | None,
        refresh_token: str | None,
        request: Request,
    ) -> None:
        self.logout_tokens.append((access_token, refresh_token))

    async def me(self, user: Any) -> Any:
        return user

    async def send_verification(self, user: Any) -> Any:
        return {"sent": True}

    async def confirm_email(self, user: Any, code: str) -> Any:
        return user

    async def request_password_reset(self, email: str, request: Request) -> Any:
        return {"accepted": True}

    async def confirm_password_reset(
        self,
        email: str,
        code: str,
        password: str,
        request: Request,
    ) -> Any:
        return {"accepted": True}


def build_app() -> tuple[FastAPI, FakeAuthApplication]:
    application = FakeAuthApplication()
    config = AuthConfig(
        secret_key="test-secret",
        cookie=CookieConfig(secure=False, same_site="lax"),
    )

    async def get_application() -> FakeAuthApplication:
        return application

    async def get_current_user() -> dict[str, Any]:
        return {"id": 1, "username": "admin"}

    app = FastAPI()
    app.include_router(
        create_auth_router(
            config=config,
            application_dependency=get_application,
            current_user_dependency=get_current_user,
            register_model=RegisterPayload,
            user_response_model=UserResponse,
        ),
        prefix="/auth",
    )
    return app, application


async def test_browser_cookie_flow_requires_csrf_for_mutations() -> None:
    app, application = build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        login = await client.post(
            "/auth/login/", json={"username": "admin", "password": "secret"}
        )
        assert login.status_code == 200
        assert login.json() == {"user": {"id": 1, "username": "admin"}}
        assert login.headers["cache-control"] == "no-store"
        assert client.cookies.get("orcestr_access") == "access"
        assert client.cookies.get("orcestr_refresh") == "refresh"
        assert "HttpOnly" in login.headers.get_list("set-cookie")[0]

        rejected = await client.post("/auth/refresh/")
        assert rejected.status_code == 403
        assert rejected.json()["detail"] == "csrf_header_missing"

        refreshed = await client.post(
            "/auth/refresh/", headers={"x-requested-with": "XMLHttpRequest"}
        )
        assert refreshed.status_code == 204
        assert application.refresh_tokens == ["refresh"]
        assert client.cookies.get("orcestr_access") == "next-access"
        assert client.cookies.get("orcestr_refresh") == "next-refresh"

        logged_out = await client.post(
            "/auth/logout/", headers={"x-requested-with": "XMLHttpRequest"}
        )
        assert logged_out.status_code == 204
        assert application.logout_tokens == [("next-access", "next-refresh")]
        assert client.cookies.get("orcestr_access") is None
        assert client.cookies.get("orcestr_refresh") is None


async def test_explicit_token_flow_and_openapi_contract() -> None:
    app, application = build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        token_login = await client.post(
            "/auth/token/login/",
            json={"username": "admin", "password": "secret"},
        )
        assert token_login.status_code == 200
        assert token_login.json()["access_token"] == "access"
        assert not token_login.headers.get_list("set-cookie")

        token_refresh = await client.post(
            "/auth/token/refresh/", json={"refresh_token": "mobile-refresh"}
        )
        assert token_refresh.status_code == 200
        assert token_refresh.json()["refresh_token"] == "next-refresh"
        assert application.refresh_tokens == ["mobile-refresh"]

        schema = (await client.get("/openapi.json")).json()
        register_schema = schema["paths"]["/auth/register/"]["post"][
            "requestBody"
        ]["content"]["application/json"]["schema"]
        token_refresh_schema = schema["paths"]["/auth/token/refresh/"]["post"][
            "requestBody"
        ]["content"]["application/json"]["schema"]
        assert register_schema["$ref"].endswith("/RegisterPayload")
        assert token_refresh_schema["$ref"].endswith("/RefreshTokenInput")
