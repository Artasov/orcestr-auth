from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status


@dataclass(frozen=True, slots=True)
class OAuthRedirectPolicy:
    allowed_origins: tuple[str, ...] = ()
    allowed_domains: tuple[str, ...] = ()
    allow_localhost: bool = False

    @staticmethod
    def clean_origin(value: str | None) -> str | None:
        raw = (value or "").strip()
        if not raw:
            return None
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}"

    def is_allowed_origin(self, value: str, request: Request) -> bool:
        origin = self.clean_origin(value)
        if origin is None:
            return False
        hostname = (urlparse(origin).hostname or "").lower()
        if self.allow_localhost and hostname in {"localhost", "127.0.0.1", "::1"}:
            return True
        configured_origins = {
            clean
            for value in self.allowed_origins
            if (clean := self.clean_origin(value)) is not None
        }
        if origin in configured_origins:
            return True
        if any(
            hostname == domain or hostname.endswith(f".{domain}")
            for domain in self.allowed_domains
            if domain and domain != "default"
        ):
            return True
        return origin == self.clean_origin(str(request.base_url))

    def origin(self, request: Request, explicit_origin: str | None) -> str:
        query_origin = self.clean_origin(explicit_origin)
        if query_origin and self.is_allowed_origin(query_origin, request):
            return query_origin
        if explicit_origin:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "oauth_origin_not_allowed")
        header_origin = self.clean_origin(request.headers.get("origin"))
        if header_origin and self.is_allowed_origin(header_origin, request):
            return header_origin
        return self.clean_origin(str(request.base_url)) or ""

    def redirect_uri(
        self,
        request: Request,
        provider: str,
        explicit_origin: str | None,
    ) -> str:
        return f"{self.origin(request, explicit_origin)}/auth/oauth/{provider}/callback"

    def validate_callback_uri(
        self,
        request: Request,
        provider: str,
        redirect_uri: str,
    ) -> None:
        parsed = urlparse(redirect_uri)
        origin = self.clean_origin(redirect_uri)
        if (
            origin is None
            or not self.is_allowed_origin(origin, request)
            or parsed.path != f"/auth/oauth/{provider}/callback"
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "oauth_redirect_uri_not_allowed",
            )
