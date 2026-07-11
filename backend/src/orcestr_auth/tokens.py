from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt

from .config import AuthConfig


class TokenPayloadError(ValueError):
    pass


class TokenCodec:
    def __init__(self, config: AuthConfig):
        self.config = config

    def create_access_token(
        self,
        user_id: int | str,
        *,
        session_id: str | None = None,
    ) -> str:
        expires_at = datetime.now(UTC) + timedelta(
            minutes=self.config.access_token_minutes
        )
        return self._create(
            user_id,
            "access",
            expires_at,
            session_id=session_id,
        )

    def create_websocket_ticket(self, user_id: int | str, ticket_id: str) -> str:
        expires_at = datetime.now(UTC) + timedelta(
            seconds=self.config.websocket_ticket_seconds
        )
        return self._create(user_id, "ws_ticket", expires_at, token_id=ticket_id)

    def decode(
        self,
        token: str,
        expected_type: str | tuple[str, ...],
    ) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience,
            )
        except JWTError as exc:
            raise TokenPayloadError("Invalid token.") from exc
        allowed = (expected_type,) if isinstance(expected_type, str) else expected_type
        if payload.get("type") not in allowed:
            raise TokenPayloadError("Invalid token type.")
        if not isinstance(payload.get("sub"), str) or not payload.get("jti"):
            raise TokenPayloadError("Invalid token payload.")
        return payload

    def _create(
        self,
        user_id: int | str,
        token_type: str,
        expires_at: datetime,
        *,
        session_id: str | None = None,
        token_id: str | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "type": token_type,
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "iat": datetime.now(UTC),
            "exp": expires_at,
            "jti": token_id or uuid4().hex,
        }
        if session_id is not None:
            payload["sid"] = session_id
        return jwt.encode(
            payload,
            self.config.secret_key,
            algorithm=self.config.algorithm,
        )
