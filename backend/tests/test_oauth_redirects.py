import pytest
from fastapi import HTTPException
from starlette.requests import Request

from orcestr_auth.fastapi import OAuthRedirectPolicy


def request(base_host: str = "api.example.com") -> Request:
    return Request(
        {
            "type": "http",
            "scheme": "https",
            "server": (base_host, 443),
            "path": "/api/v1/auth/methods/",
            "headers": [(b"host", base_host.encode())],
        }
    )


def test_callback_policy_accepts_configured_subdomains() -> None:
    policy = OAuthRedirectPolicy(allowed_domains=("example.com",))
    callback = "https://beauty.example.com/auth/oauth/github/callback"
    policy.validate_callback_uri(request(), "github", callback)


def test_callback_policy_rejects_external_and_wrong_paths() -> None:
    policy = OAuthRedirectPolicy(allowed_domains=("example.com",))
    with pytest.raises(HTTPException):
        policy.validate_callback_uri(
            request(),
            "google",
            "https://evil.test/auth/oauth/google/callback",
        )
    with pytest.raises(HTTPException):
        policy.validate_callback_uri(
            request(),
            "google",
            "https://app.example.com/auth/oauth/yandex/callback",
        )
