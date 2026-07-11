from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel

from ..config import AuthConfig
from ..contracts import (
    AuthTokens,
    EmailCodeInput,
    LoginInput,
    OAuthCallbackInput,
    PasswordResetConfirmInput,
    PasswordResetRequestInput,
    RefreshTokenInput,
    RegisterInput,
)
from ..cookies import clear_auth_cookies, set_auth_cookies


@dataclass(frozen=True, slots=True)
class AuthResult:
    user: Any
    tokens: AuthTokens


class AuthHttpApplication(Protocol):
    async def register(self, payload: BaseModel, request: Request) -> AuthResult: ...
    async def login(self, payload: LoginInput, request: Request) -> AuthResult: ...
    async def oauth(
        self, provider: str, payload: OAuthCallbackInput, request: Request
    ) -> AuthResult: ...
    async def refresh(
        self, refresh_token: str | None, request: Request
    ) -> AuthTokens: ...
    async def logout(
        self,
        *,
        access_token: str | None,
        refresh_token: str | None,
        request: Request,
    ) -> None: ...
    async def me(self, user: Any) -> Any: ...
    async def send_verification(self, user: Any) -> Any: ...
    async def confirm_email(self, user: Any, code: str) -> Any: ...
    async def request_password_reset(self, email: str, request: Request) -> Any: ...
    async def confirm_password_reset(
        self,
        email: str,
        code: str,
        password: str,
        request: Request,
    ) -> Any: ...


def create_auth_router(
    *,
    config: AuthConfig,
    application_dependency: Callable[..., Awaitable[AuthHttpApplication]],
    current_user_dependency: Callable[..., Any],
    register_model: type[BaseModel] = RegisterInput,
    login_model: type[BaseModel] = LoginInput,
    oauth_callback_model: type[BaseModel] = OAuthCallbackInput,
    email_code_model: type[BaseModel] = EmailCodeInput,
    password_reset_request_model: type[BaseModel] = PasswordResetRequestInput,
    password_reset_confirm_model: type[BaseModel] = PasswordResetConfirmInput,
    refresh_token_model: type[BaseModel] = RefreshTokenInput,
    user_response_model: Any = None,
    token_response_model: Any = AuthTokens,
    verification_response_model: Any = None,
    password_reset_response_model: Any = None,
) -> APIRouter:
    """Create common auth HTTP routes while leaving product hooks in the app."""

    router = APIRouter()

    async def register(
        payload: Any,
        request: Request,
        response: Response,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> dict[str, Any]:
        result = await application.register(payload, request)
        _start_browser_session(response, result.tokens, config)
        return {"user": result.user}

    register.__annotations__["payload"] = register_model
    router.add_api_route(
        "/register/",
        register,
        methods=["POST"],
        response_model=_browser_response_model(user_response_model),
    )

    async def login(
        payload: Any,
        request: Request,
        response: Response,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> dict[str, Any]:
        result = await application.login(payload, request)
        _start_browser_session(response, result.tokens, config)
        return {"user": result.user}

    login.__annotations__["payload"] = login_model
    router.add_api_route(
        "/login/",
        login,
        methods=["POST"],
        response_model=_browser_response_model(user_response_model),
    )

    async def oauth(
        provider: str,
        payload: Any,
        request: Request,
        response: Response,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> dict[str, Any]:
        result = await application.oauth(provider, payload, request)
        _start_browser_session(response, result.tokens, config)
        return {"user": result.user}

    oauth.__annotations__["payload"] = oauth_callback_model
    router.add_api_route(
        "/oauth/{provider}/callback/",
        oauth,
        methods=["POST"],
        response_model=_browser_response_model(user_response_model),
    )

    @router.post("/refresh/", status_code=status.HTTP_204_NO_CONTENT)
    async def refresh(
        request: Request,
        response: Response,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> Response:
        _require_cookie_csrf(request, config)
        tokens = await application.refresh(
            request.cookies.get(config.cookie.refresh_name), request
        )
        _start_browser_session(response, tokens, config)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    async def token_login(
        payload: Any,
        request: Request,
        response: Response,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> AuthTokens:
        result = await application.login(payload, request)
        response.headers["Cache-Control"] = "no-store"
        return result.tokens

    token_login.__annotations__["payload"] = login_model
    router.add_api_route(
        "/token/login/",
        token_login,
        methods=["POST"],
        response_model=token_response_model,
    )

    async def token_refresh(
        payload: Any,
        request: Request,
        response: Response,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> AuthTokens:
        tokens = await application.refresh(payload.refresh_token, request)
        response.headers["Cache-Control"] = "no-store"
        return tokens

    token_refresh.__annotations__["payload"] = refresh_token_model
    router.add_api_route(
        "/token/refresh/",
        token_refresh,
        methods=["POST"],
        response_model=token_response_model,
    )

    @router.post("/logout/", status_code=status.HTTP_204_NO_CONTENT)
    async def logout(
        request: Request,
        response: Response,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> Response:
        _require_cookie_csrf(request, config)
        await application.logout(
            access_token=request.cookies.get(config.cookie.access_name),
            refresh_token=request.cookies.get(config.cookie.refresh_name),
            request=request,
        )
        clear_auth_cookies(response, config)
        response.headers["Cache-Control"] = "no-store"
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get("/me/", response_model=user_response_model)
    async def me(
        current_user: Any = Depends(current_user_dependency),
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> Any:
        return await application.me(current_user)

    @router.post(
        "/email/verification-code/",
        response_model=verification_response_model,
    )
    async def send_verification(
        current_user: Any = Depends(current_user_dependency),
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> Any:
        return await application.send_verification(current_user)

    async def confirm_email(
        payload: Any,
        current_user: Any = Depends(current_user_dependency),
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> Any:
        return await application.confirm_email(current_user, payload.code)

    confirm_email.__annotations__["payload"] = email_code_model
    router.add_api_route(
        "/email/confirm/",
        confirm_email,
        methods=["POST"],
        response_model=user_response_model,
    )

    async def request_password_reset(
        payload: Any,
        request: Request,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> Any:
        return await application.request_password_reset(payload.email, request)

    request_password_reset.__annotations__["payload"] = password_reset_request_model
    router.add_api_route(
        "/password/reset/request/",
        request_password_reset,
        methods=["POST"],
        response_model=password_reset_response_model,
        status_code=status.HTTP_202_ACCEPTED,
    )

    async def confirm_password_reset(
        payload: Any,
        request: Request,
        application: AuthHttpApplication = Depends(application_dependency),
    ) -> Any:
        return await application.confirm_password_reset(
            payload.email,
            payload.code,
            payload.password,
            request,
        )

    confirm_password_reset.__annotations__["payload"] = password_reset_confirm_model
    router.add_api_route(
        "/password/reset/confirm/",
        confirm_password_reset,
        methods=["POST"],
        response_model=password_reset_response_model,
    )

    return router


def _start_browser_session(
    response: Response,
    tokens: AuthTokens,
    config: AuthConfig,
) -> None:
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token, config)
    response.headers["Cache-Control"] = "no-store"


def _require_cookie_csrf(request: Request, config: AuthConfig) -> None:
    if not (
        request.cookies.get(config.cookie.access_name)
        or request.cookies.get(config.cookie.refresh_name)
    ):
        return
    if request.headers.get("x-requested-with", "").lower() != "xmlhttprequest":
        from fastapi import HTTPException

        raise HTTPException(status.HTTP_403_FORBIDDEN, "csrf_header_missing")


def _browser_response_model(user_model: Any) -> Any:
    if user_model is None:
        return None
    from pydantic import create_model

    return create_model("BrowserAuthResponse", user=(user_model, ...))
