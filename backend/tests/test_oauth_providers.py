import httpx
import pytest

from orcestr_auth import AuthConfig, OAuthClientConfig
from orcestr_auth.contracts import OAuthCallbackInput
from orcestr_auth.oauth import OAuthProviderClient, OAuthProviderError


def config(provider: str) -> AuthConfig:
    return AuthConfig(
        secret_key="secret",
        oauth={provider: OAuthClientConfig("client-id", "client-secret")},
    )


@pytest.mark.parametrize(
    ("provider", "responses", "expected_id"),
    [
        (
            "google",
            {
                "oauth2.googleapis.com": {"access_token": "token"},
                "openidconnect.googleapis.com": {
                    "sub": "google-1",
                    "email": "user@example.com",
                    "email_verified": True,
                },
            },
            "google-1",
        ),
        (
            "yandex",
            {
                "oauth.yandex.ru": {"access_token": "token"},
                "login.yandex.ru": {
                    "id": "yandex-1",
                    "default_email": "user@example.com",
                },
            },
            "yandex-1",
        ),
    ],
)
async def test_google_and_yandex_profiles(
    provider: str,
    responses: dict[str, dict],
    expected_id: str,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=responses[request.url.host])
    )
    profile = await OAuthProviderClient(
        config(provider), transport=transport
    ).exchange(
        provider,
        OAuthCallbackInput(
            code="code",
            redirect_uri=f"https://app.example/auth/oauth/{provider}/callback",
            code_verifier="verifier",
        ),
    )
    assert profile.provider_user_id == expected_id
    assert profile.email == "user@example.com"


async def test_github_uses_verified_primary_email() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "github.com":
            return httpx.Response(200, json={"access_token": "token"})
        if request.url.path.endswith("/emails"):
            return httpx.Response(
                200,
                json=[
                    {
                        "email": "user@example.com",
                        "primary": True,
                        "verified": True,
                    }
                ],
            )
        return httpx.Response(200, json={"id": 17, "name": "Demo User"})

    profile = await OAuthProviderClient(
        config("github"), transport=httpx.MockTransport(handler)
    ).exchange(
        "github",
        OAuthCallbackInput(
            code="code",
            redirect_uri="https://app.example/auth/oauth/github/callback",
            code_verifier="verifier",
        ),
    )
    assert profile.provider_user_id == "17"
    assert profile.email == "user@example.com"
    assert profile.email_verified is True


async def test_disabled_provider_is_rejected_without_network_request() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    client = OAuthProviderClient(
        AuthConfig(secret_key="secret"),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(OAuthProviderError, match="oauth_provider_not_enabled"):
        await client.exchange(
            "google",
            OAuthCallbackInput(
                code="code",
                redirect_uri="https://app.example/auth/oauth/google/callback",
            ),
        )
    assert called is False
