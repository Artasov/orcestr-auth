from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import AuthConfig
from ..sqlalchemy import AuthModelSet
from ..tokens import TokenCodec, TokenPayloadError


class WebSocketTicketService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        models: AuthModelSet,
        config: AuthConfig,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.db = session
        self.models = models
        self.config = config
        self.codec = TokenCodec(config)
        self.now = now

    async def issue(self, user_id: Any) -> str:
        ticket_id = secrets.token_hex(16)
        self.db.add(
            self.models.websocket_ticket(
                id=ticket_id,
                user_id=user_id,
                expires_at=self.now()
                + timedelta(seconds=self.config.websocket_ticket_seconds),
            )
        )
        await self.db.flush()
        return self.codec.create_websocket_ticket(user_id, ticket_id)

    async def consume(self, token: str) -> Any:
        payload = self.codec.decode(token, "ws_ticket")
        ticket_id = str(payload["jti"])
        ticket = await self.db.get(self.models.websocket_ticket, ticket_id)
        now = self.now()
        if (
            ticket is None
            or ticket.used_at is not None
            or _aware(ticket.expires_at) <= now
            or str(ticket.user_id) != payload["sub"]
        ):
            raise TokenPayloadError("Invalid WebSocket ticket.")
        ticket.used_at = now
        await self.db.flush()
        return ticket.user_id


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
