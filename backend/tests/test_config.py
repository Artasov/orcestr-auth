from orcestr_auth import AuthConfig, OAuth2ClientConfig, OAuthClientConfig


def test_only_configured_oauth_providers_are_enabled() -> None:
    config = AuthConfig(
        secret_key="secret",
        oauth={
            "google": OAuthClientConfig("id", "secret"),
            "github": OAuthClientConfig("id", "secret"),
        },
    )
    assert config.enabled_oauth_providers == ("github", "google")


def test_registered_oauth2_clients_are_separate_from_social_providers() -> None:
    client = OAuth2ClientConfig(
        display_name="Orcestr Real Translate",
        redirect_uris=("com.orcestr.realtranslate://oauth/callback",),
        scopes=("profile",),
    )
    config = AuthConfig(
        secret_key="secret",
        oauth2_clients={"orcestr-real-translate": client},
    )
    assert config.oauth == {}
    assert config.oauth2_clients["orcestr-real-translate"] is client
    assert client.enabled is True
    assert client.pkce_required is True
