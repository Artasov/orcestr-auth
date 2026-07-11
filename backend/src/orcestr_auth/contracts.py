from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


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
