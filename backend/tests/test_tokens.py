from datetime import UTC, datetime

import pytest

from orcestr_auth import AuthConfig, TokenCodec, TokenPayloadError


def test_access_token_contains_required_claims() -> None:
    codec = TokenCodec(AuthConfig(secret_key="test-secret"))
    token = codec.create_access_token(42, session_id="session-1")
    payload = codec.decode(token, "access")
    assert payload["sub"] == "42"
    assert payload["sid"] == "session-1"
    assert payload["iss"] == "orcestr"
    assert payload["aud"] == "orcestr-api"
    assert payload["jti"]
    assert datetime.fromtimestamp(payload["iat"], UTC) <= datetime.now(UTC)


def test_token_type_is_enforced() -> None:
    codec = TokenCodec(AuthConfig(secret_key="test-secret"))
    ticket = codec.create_websocket_ticket(1, "ticket")
    with pytest.raises(TokenPayloadError):
        codec.decode(ticket, "access")

