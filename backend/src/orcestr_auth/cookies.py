from __future__ import annotations

from fastapi import Response

from .config import AuthConfig


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    config: AuthConfig,
) -> None:
    cookie = config.cookie
    response.set_cookie(
        cookie.access_name,
        access_token,
        max_age=config.access_token_minutes * 60,
        httponly=True,
        samesite=cookie.same_site,
        secure=cookie.secure,
        path=cookie.path,
        domain=cookie.domain,
    )
    response.set_cookie(
        cookie.refresh_name,
        refresh_token,
        max_age=config.refresh_token_days * 24 * 60 * 60,
        httponly=True,
        samesite=cookie.same_site,
        secure=cookie.secure,
        path=cookie.path,
        domain=cookie.domain,
    )


def clear_auth_cookies(response: Response, config: AuthConfig) -> None:
    cookie = config.cookie
    response.delete_cookie(
        cookie.access_name,
        path=cookie.path,
        domain=cookie.domain,
        secure=cookie.secure,
        httponly=True,
        samesite=cookie.same_site,
    )
    response.delete_cookie(
        cookie.refresh_name,
        path=cookie.path,
        domain=cookie.domain,
        secure=cookie.secure,
        httponly=True,
        samesite=cookie.same_site,
    )

