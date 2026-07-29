from __future__ import annotations

import json
from pathlib import Path

from orcestr_auth.errors import AUTH_ERROR_MESSAGES, AuthErrorCode, auth_api_error

AUTH_ERROR_CODES = (
    Path(__file__).parents[2] / "contracts" / "auth-error-codes.json"
)


def test_every_auth_code_has_a_safe_default_message() -> None:
    assert set(AUTH_ERROR_MESSAGES) == set(AuthErrorCode)
    assert all(message.strip() for message in AUTH_ERROR_MESSAGES.values())


def test_auth_api_error_preserves_the_stable_code() -> None:
    error = auth_api_error(
        status_code=401,
        code=AuthErrorCode.INVALID_CREDENTIALS,
    )
    assert error.status_code == 401
    assert error.code == "invalid_credentials"
    assert error.message == "Invalid username or password."


def test_python_auth_codes_match_the_shared_contract() -> None:
    contract = json.loads(AUTH_ERROR_CODES.read_text(encoding="utf-8"))
    assert set(contract) == {code.value for code in AuthErrorCode}
