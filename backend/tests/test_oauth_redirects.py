import pytest
from orcestr_core import ApiError
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
    callback = "https://account.example.com/auth/oauth/github/callback"
    policy.validate_callback_uri(request(), "github", callback)


def test_callback_policy_rejects_external_and_wrong_paths() -> None:
    policy = OAuthRedirectPolicy(allowed_domains=("example.com",))
    with pytest.raises(ApiError) as external:
        policy.validate_callback_uri(
            request(),
            "google",
            "https://evil.test/auth/oauth/google/callback",
        )
    assert external.value.code == "oauth_redirect_uri_not_allowed"
    with pytest.raises(ApiError) as wrong_path:
        policy.validate_callback_uri(
            request(),
            "google",
            "https://app.example.com/auth/oauth/yandex/callback",
        )
    assert wrong_path.value.code == "oauth_redirect_uri_not_allowed"
