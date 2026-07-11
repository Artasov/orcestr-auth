from orcestr_auth import AuthConfig, OAuthClientConfig


def test_only_configured_oauth_providers_are_enabled() -> None:
    config = AuthConfig(
        secret_key="secret",
        oauth={
            "google": OAuthClientConfig("id", "secret"),
            "github": OAuthClientConfig("id", "secret"),
        },
    )
    assert config.enabled_oauth_providers == ("github", "google")
