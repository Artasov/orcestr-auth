from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute


@dataclass(frozen=True, slots=True)
class UserFieldMap:
    id: InstrumentedAttribute[Any]
    username: InstrumentedAttribute[Any]
    email: InstrumentedAttribute[Any]
    password_hash: InstrumentedAttribute[Any]
    is_active: InstrumentedAttribute[Any]
    email_verified_at: InstrumentedAttribute[Any] | None = None


class SqlAlchemyUserRepository:
    """Direct indexed access to the consumer-owned SQLAlchemy user model."""

    def __init__(
        self,
        session: AsyncSession,
        model: type[Any],
        fields: UserFieldMap,
    ) -> None:
        self.session = session
        self.model = model
        self.fields = fields

    async def get_by_id(self, user_id: Any) -> Any | None:
        return await self.session.scalar(
            select(self.model).where(self.fields.id == user_id)
        )

    async def get_by_username(self, username: str) -> Any | None:
        normalized = username.strip().lower()
        return await self.session.scalar(
            select(self.model).where(self.fields.username == normalized)
        )

    async def get_by_email(self, email: str) -> Any | None:
        normalized = email.strip().lower()
        return await self.session.scalar(
            select(self.model).where(self.fields.email == normalized)
        )

    async def get_by_login(self, login: str) -> Any | None:
        normalized = login.strip().lower()
        return await self.session.scalar(
            select(self.model).where(
                or_(
                    self.fields.username == normalized,
                    self.fields.email == normalized,
                )
            )
        )

    def user_id(self, user: Any) -> Any:
        return getattr(user, self.fields.id.key)

    def password_hash(self, user: Any) -> str:
        return str(getattr(user, self.fields.password_hash.key))

    def set_password_hash(self, user: Any, value: str) -> None:
        setattr(user, self.fields.password_hash.key, value)

    def is_active(self, user: Any) -> bool:
        return bool(getattr(user, self.fields.is_active.key))

    def email(self, user: Any) -> str | None:
        value = getattr(user, self.fields.email.key)
        return str(value).strip().lower() if value else None

    def mark_email_verified(self, user: Any, verified_at: Any) -> None:
        if self.fields.email_verified_at is None:
            return
        setattr(user, self.fields.email_verified_at.key, verified_at)

