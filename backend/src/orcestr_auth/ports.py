"""Small extension ports for product-specific auth behaviour."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol


class Clock(Protocol):
    def __call__(self) -> datetime: ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: Any) -> Any | None: ...
    async def get_by_login(self, login: str) -> Any | None: ...
    def user_id(self, user: Any) -> Any: ...
    def password_hash(self, user: Any) -> str: ...
    def set_password_hash(self, user: Any, value: str) -> None: ...
    def is_active(self, user: Any) -> bool: ...


class RateLimiter(Protocol):
    async def check(
        self,
        *,
        action: str,
        identifier: str,
        context: Mapping[str, Any] | None = None,
    ) -> None: ...


class AuditSink(Protocol):
    async def record(
        self,
        *,
        action: str,
        user_id: Any | None = None,
        identifier: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None: ...
