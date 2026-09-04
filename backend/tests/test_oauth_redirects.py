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


@pytest.mark.parametrize(
    "host",
    ["localhost", "127.0.0.1", "[::1]", "deliveries.localhost", "beauty.localhost"],
)
def test_local_origins_require_explicit_development_opt_in(host: str) -> None:
    origin = f"http://{host}:8934"
    policy = OAuthRedirectPolicy(allow_localhost=True)
    assert policy.origin(request(), origin) == origin
    policy.validate_callback_uri(request(), "google", f"{origin}/auth/oauth/google/callback")
    with pytest.raises(ApiError):
        OAuthRedirectPolicy().origin(request(), origin)


@pytest.mark.parametrize(
    "host", ["notlocalhost", "localhost.evil.test", "deliveries.localhost.evil.test"],
)
def test_local_origin_policy_rejects_lookalike_hosts(host: str) -> None:
    with pytest.raises(ApiError):
        OAuthRedirectPolicy(allow_localhost=True).origin(request(), f"http://{host}:8934")


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
