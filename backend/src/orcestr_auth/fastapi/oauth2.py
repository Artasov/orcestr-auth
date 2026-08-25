from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Awaitable, Callable, Protocol, TypeVar
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from ..config import AuthConfig
from ..contracts import (
    OAuth2AuthorizationContext,
    OAuth2AuthorizationRequest,
    OAuth2AuthorizationResponse,
    OAuth2RevocationRequest,
    OAuth2TokenRequest,
    OAuth2TokenResponse,
)
from ..services.oauth2 import OAuth2ErrorCode, OAuth2ProtocolError
from .dependencies import OAuth2Principal

_NO_STORE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
}
_MAX_REQUEST_BODY = 16 * 1024
ModelT = TypeVar("ModelT", bound=BaseModel)


class OAuth2HttpApplication(Protocol):
    def context(
        self,
        payload: OAuth2AuthorizationRequest,
    ) -> OAuth2AuthorizationContext: ...

    async def authorize(
        self,
        payload: OAuth2AuthorizationRequest,
        user: Any,
    ) -> OAuth2AuthorizationResponse: ...

    async def token(
        self,
        payload: OAuth2TokenRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> OAuth2TokenResponse: ...

    async def revoke(self, *, client_id: str, token: str) -> bool: ...

    async def userinfo(self, principal: OAuth2Principal) -> Any: ...


def create_oauth2_router(
    *,
    config: AuthConfig,
    application_dependency: Callable[..., Awaitable[OAuth2HttpApplication]],
    current_user_dependency: Callable[..., Any],
    oauth2_principal_dependency: Callable[..., Any] | None = None,
    userinfo_response_model: type[Any] | None = None,
) -> APIRouter:
    """Create OAuth 2.1 public-client endpoints.

    Mount this router below a consumer-controlled prefix, for example
    ``/api/v1/auth/oauth2``.
    """

    router = APIRouter()

    @router.get(
        "/authorize/",
        response_model=OAuth2AuthorizationContext,
        openapi_extra={
            "parameters": _query_openapi(OAuth2AuthorizationRequest),
        },
    )
    async def authorization_context(
        request: Request,
        response: Response,
        application: OAuth2HttpApplication = Depends(application_dependency),
    ) -> Any:
        try:
            payload = _query_model(request, OAuth2AuthorizationRequest)
            result = application.context(payload)
        except OAuth2ProtocolError as exc:
            return _error_response(exc)
        response.headers.update(_NO_STORE_HEADERS)
        return result

    @router.post(
        "/authorize/",
        response_model=OAuth2AuthorizationResponse,
        openapi_extra={
            "requestBody": _request_body_openapi(OAuth2AuthorizationRequest),
        },
    )
    async def authorize(
        request: Request,
        response: Response,
        current_user: Any = Depends(current_user_dependency),
        application: OAuth2HttpApplication = Depends(application_dependency),
    ) -> Any:
        try:
            _require_authorize_csrf(request, config)
            payload = await _body_model(request, OAuth2AuthorizationRequest)
            result = await application.authorize(payload, current_user)
        except OAuth2ProtocolError as exc:
            return _error_response(exc)
        response.headers.update(_NO_STORE_HEADERS)
        return result

    @router.post(
        "/token/",
        response_model=OAuth2TokenResponse,
        response_model_exclude_none=True,
        openapi_extra={
            "requestBody": _request_body_openapi(OAuth2TokenRequest),
        },
    )
    async def token(
        request: Request,
        response: Response,
        application: OAuth2HttpApplication = Depends(application_dependency),
    ) -> Any:
        try:
            payload = await _body_model(request, OAuth2TokenRequest)
            result = await application.token(
                payload,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except OAuth2ProtocolError as exc:
            return _error_response(exc)
        response.headers.update(_NO_STORE_HEADERS)
        return result

    @router.post(
        "/revoke/",
        status_code=200,
        openapi_extra={
            "requestBody": _request_body_openapi(OAuth2RevocationRequest),
        },
    )
    async def revoke(
        request: Request,
        application: OAuth2HttpApplication = Depends(application_dependency),
    ) -> Response:
        try:
            payload = await _body_model(request, OAuth2RevocationRequest)
            await application.revoke(
                client_id=payload.client_id,
                token=payload.token,
            )
        except OAuth2ProtocolError as exc:
            return _error_response(exc)
        return Response(status_code=200, headers=_NO_STORE_HEADERS)

    if oauth2_principal_dependency is not None:

        @router.get(
            "/userinfo/",
            response_model=userinfo_response_model,
        )
        async def userinfo(
            response: Response,
            principal: OAuth2Principal = Depends(oauth2_principal_dependency),
            application: OAuth2HttpApplication = Depends(application_dependency),
        ) -> Any:
            result = await application.userinfo(principal)
            response.headers.update(_NO_STORE_HEADERS)
            return result

    return router


def _query_model(request: Request, model: type[ModelT]) -> ModelT:
    return _validate_model(_unique_items(request.query_params.multi_items()), model)


async def _body_model(request: Request, model: type[ModelT]) -> ModelT:
    body = await request.body()
    if len(body) > _MAX_REQUEST_BODY:
        raise _invalid_request("The request body is too large.")
    content_type = request.headers.get("content-type", "").partition(";")[0].lower()
    try:
        if content_type == "application/json":
            data = json.loads(body or b"{}")
            if not isinstance(data, dict):
                raise _invalid_request("The JSON request body must be an object.")
        elif content_type == "application/x-www-form-urlencoded":
            data = _unique_items(
                parse_qsl(
                    body.decode("utf-8"),
                    keep_blank_values=True,
                    strict_parsing=True,
                )
            )
        else:
            raise _invalid_request(
                "Use application/json or application/x-www-form-urlencoded."
            )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, OAuth2ProtocolError):
            raise
        raise _invalid_request("The request body is malformed.") from exc
    return _validate_model(data, model)


def _validate_model(data: Mapping[str, Any], model: type[ModelT]) -> ModelT:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise _invalid_request("Required OAuth parameters are missing or invalid.") from exc


def _unique_items(items: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in items:
        if key in result:
            raise _invalid_request(f"OAuth parameter {key!r} must not be repeated.")
        result[key] = value
    return result


def _require_authorize_csrf(request: Request, config: AuthConfig) -> None:
    has_auth_cookie = bool(
        request.cookies.get(config.cookie.access_name)
        or request.cookies.get(config.cookie.refresh_name)
    )
    if has_auth_cookie and request.headers.get(
        "x-requested-with", ""
    ).lower() != "xmlhttprequest":
        raise OAuth2ProtocolError(
            OAuth2ErrorCode.ACCESS_DENIED,
            "The request security check failed.",
            status_code=403,
        )


def _invalid_request(description: str) -> OAuth2ProtocolError:
    return OAuth2ProtocolError(OAuth2ErrorCode.INVALID_REQUEST, description)


def _error_response(exc: OAuth2ProtocolError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error.value,
            "error_description": exc.description,
        },
        headers=_NO_STORE_HEADERS,
    )


def _request_body_openapi(model: type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    return {
        "required": True,
        "content": {
            "application/json": {"schema": schema},
            "application/x-www-form-urlencoded": {"schema": schema},
        },
    }


def _query_openapi(model: type[BaseModel]) -> list[dict[str, Any]]:
    model_schema = model.model_json_schema()
    required = set(model_schema.get("required", ()))
    return [
        {
            "name": name,
            "in": "query",
            "required": name in required,
            "schema": schema,
        }
        for name, schema in model_schema.get("properties", {}).items()
    ]
