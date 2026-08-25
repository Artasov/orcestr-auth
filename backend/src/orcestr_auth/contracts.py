from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenInput(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=2048)


class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


class RegisterInput(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=8, max_length=1024)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)


class PasswordResetRequestInput(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class PasswordResetConfirmInput(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    code: str = Field(min_length=4, max_length=32)
    password: str = Field(min_length=8, max_length=1024)


class OAuthCallbackInput(BaseModel):
    code: str
    redirect_uri: str
    code_verifier: str | None = None
    state: str | None = None


class OAuthPublicProvider(BaseModel):
    provider: str
    client_id: str


class _OAuth2Request(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OAuth2AuthorizationRequest(_OAuth2Request):
    response_type: str = Field(min_length=1, max_length=32)
    client_id: str = Field(min_length=1, max_length=128)
    redirect_uri: str = Field(min_length=1, max_length=2048)
    scope: str = Field(default="", max_length=1024)
    state: str = Field(min_length=16, max_length=512)
    code_challenge: str = Field(min_length=43, max_length=128)
    code_challenge_method: str = Field(min_length=1, max_length=16)


class OAuth2AuthorizationContext(BaseModel):
    client_id: str
    display_name: str
    redirect_uri: str
    requested_scopes: tuple[str, ...]
    state: str
    code_challenge: str
    code_challenge_method: Literal["S256"] = "S256"


class OAuth2AuthorizationResponse(BaseModel):
    redirect_uri: str


class OAuth2TokenRequest(_OAuth2Request):
    grant_type: str = Field(min_length=1, max_length=64)
    client_id: str = Field(min_length=1, max_length=128)
    code: str | None = Field(default=None, min_length=1, max_length=512)
    redirect_uri: str | None = Field(default=None, min_length=1, max_length=2048)
    code_verifier: str | None = Field(default=None, min_length=1, max_length=256)
    refresh_token: str | None = Field(default=None, min_length=1, max_length=2048)
    scope: str | None = Field(default=None, max_length=1024)


class OAuth2TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    scope: str = ""


class OAuth2RevocationRequest(_OAuth2Request):
    client_id: str = Field(min_length=1, max_length=128)
    token: str = Field(min_length=1, max_length=2048)
    token_type_hint: Literal["refresh_token"] | None = None


class EmailCodeInput(BaseModel):
    code: str = Field(min_length=4, max_length=32)


class RegistrationHandler(Protocol):
    async def __call__(
        self,
        *,
        session: Any,
        user: Any,
        payload: Any,
        request: Any,
    ) -> None: ...


class EmailSender(Protocol):
    async def send(
        self,
        *,
        subject: str,
        recipients: tuple[str, ...],
        plain_body: str,
        html_body: str,
    ) -> bool: ...
