from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from ..config import AuthConfig, OAuthClientConfig
from ..contracts import OAuthCallbackInput


class OAuthProviderError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class OAuthProfile:
    provider: str
    provider_user_id: str
    email: str
    email_verified: bool
    first_name: str | None = None
    last_name: str | None = None


def supported_providers() -> tuple[str, ...]:
    return ("github", "google", "yandex")


class OAuthProviderClient:
    def __init__(
        self,
        config: AuthConfig,
        *,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = config
        self.timeout = timeout
        self.transport = transport

    async def exchange(
        self,
        provider: str,
        payload: OAuthCallbackInput,
    ) -> OAuthProfile:
        normalized = provider.strip().lower()
        credentials = self.config.oauth.get(normalized)
        if normalized not in supported_providers() or credentials is None:
            raise OAuthProviderError("oauth_provider_not_enabled")
        self._validate_redirect(credentials, payload.redirect_uri)
        try:
            if normalized == "github":
                return await self._github(credentials, payload)
            if normalized == "google":
                return await self._google(credentials, payload)
            return await self._yandex(credentials, payload)
        except httpx.TimeoutException as exc:
            raise OAuthProviderError("oauth_provider_timeout") from exc
        except httpx.RequestError as exc:
            raise OAuthProviderError("oauth_provider_unavailable") from exc

    @staticmethod
    def _validate_redirect(config: OAuthClientConfig, redirect_uri: str) -> None:
        if not config.redirect_origins:
            return
        origin = httpx.URL(redirect_uri).copy_with(path="/", query=None, fragment=None)
        allowed = {
            str(httpx.URL(value).copy_with(path="/", query=None, fragment=None))
            for value in config.redirect_origins
        }
        if str(origin) not in allowed:
            raise OAuthProviderError("oauth_redirect_not_allowed")

    async def _google(
        self,
        credentials: OAuthClientConfig,
        payload: OAuthCallbackInput,
    ) -> OAuthProfile:
        async with httpx.AsyncClient(
            timeout=self.timeout, transport=self.transport
        ) as client:
            token = await client.post(
                "https://oauth2.googleapis.com/token",
                data=self._token_data(credentials, payload),
            )
            access_token = self._access_token(token)
            response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        data = self._json(response, "oauth_userinfo_failed")
        return self._profile(
            "google",
            data,
            identifier=data.get("sub"),
            verified=data.get("email_verified") in (True, "true", "1"),
        )

    async def _github(
        self,
        credentials: OAuthClientConfig,
        payload: OAuthCallbackInput,
    ) -> OAuthProfile:
        async with httpx.AsyncClient(
            timeout=self.timeout, transport=self.transport
        ) as client:
            token = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data=self._token_data(credentials, payload),
            )
            access_token = self._access_token(token)
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            user_response = await client.get("https://api.github.com/user", headers=headers)
            emails_response = await client.get(
                "https://api.github.com/user/emails", headers=headers
            )
        user = self._json(user_response, "oauth_userinfo_failed")
        emails = self._json(emails_response, "oauth_userinfo_failed")
        selected = next(
            (
                item
                for item in emails
                if isinstance(item, dict)
                and item.get("primary") is True
                and item.get("verified") is True
            ),
            None,
        )
        if selected is None:
            selected = next(
                (
                    item
                    for item in emails
                    if isinstance(item, dict) and item.get("verified") is True
                ),
                None,
            )
        email = str((selected or {}).get("email") or user.get("email") or "").lower()
        name = str(user.get("name") or "").strip().split(maxsplit=1)
        return self._profile(
            "github",
            {"email": email},
            identifier=user.get("id"),
            verified=bool(selected),
            first_name=name[0] if name else None,
            last_name=name[1] if len(name) > 1 else None,
        )

    async def _yandex(
        self,
        credentials: OAuthClientConfig,
        payload: OAuthCallbackInput,
    ) -> OAuthProfile:
        async with httpx.AsyncClient(
            timeout=self.timeout, transport=self.transport
        ) as client:
            token = await client.post(
                "https://oauth.yandex.ru/token",
                data=self._token_data(credentials, payload),
            )
            access_token = self._access_token(token)
            response = await client.get(
                "https://login.yandex.ru/info",
                params={"format": "json"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        data = self._json(response, "oauth_userinfo_failed")
        emails = data.get("emails") if isinstance(data.get("emails"), list) else []
        email = str(data.get("default_email") or (emails[0] if emails else "")).lower()
        return self._profile(
            "yandex",
            {"email": email},
            identifier=data.get("id"),
            verified=True,
            first_name=str(data.get("first_name") or "") or None,
            last_name=str(data.get("last_name") or "") or None,
        )

    @staticmethod
    def _token_data(
        credentials: OAuthClientConfig,
        payload: OAuthCallbackInput,
    ) -> dict[str, str]:
        result = {
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "code": payload.code,
            "redirect_uri": payload.redirect_uri,
            "grant_type": "authorization_code",
        }
        if payload.code_verifier:
            result["code_verifier"] = payload.code_verifier
        return result

    @staticmethod
    def _access_token(response: httpx.Response) -> str:
        data = OAuthProviderClient._json(response, "oauth_code_exchange_failed")
        token = str(data.get("access_token") or "")
        if not token:
            raise OAuthProviderError("oauth_access_token_missing")
        return token

    @staticmethod
    def _json(response: httpx.Response, error: str) -> Any:
        if response.status_code < 200 or response.status_code >= 300:
            raise OAuthProviderError(error)
        try:
            return response.json()
        except ValueError as exc:
            raise OAuthProviderError(error) from exc

    @staticmethod
    def _profile(
        provider: str,
        data: dict[str, Any],
        *,
        identifier: Any,
        verified: bool,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> OAuthProfile:
        email = str(data.get("email") or "").strip().lower()
        provider_user_id = str(identifier or "").strip()
        if not email or not provider_user_id:
            raise OAuthProviderError("oauth_email_missing")
        return OAuthProfile(
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            email_verified=verified,
            first_name=first_name,
            last_name=last_name,
        )
