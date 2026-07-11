from __future__ import annotations

import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class VerificationCodeError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class VerificationCodeService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        model: type[Any],
        secret_key: str,
        expire_minutes: int,
        code_length: int,
        max_attempts: int,
        resend_cooldown_seconds: int,
        namespace: str,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        code_factory: Callable[[], str] | None = None,
    ) -> None:
        self.db = session
        self.model = model
        self.secret_key = secret_key
        self.expire_minutes = expire_minutes
        self.code_length = max(code_length, 4)
        self.max_attempts = max_attempts
        self.resend_cooldown_seconds = resend_cooldown_seconds
        self.namespace = namespace
        self.now = now
        self.code_factory = code_factory

    async def issue(self, user_id: Any, email: str) -> str | None:
        normalized_email = email.strip().lower()
        now = self.now()
        latest = await self._latest(user_id, normalized_email)
        if latest is not None:
            created_at = _aware(latest.created_at)
            if created_at + timedelta(seconds=self.resend_cooldown_seconds) > now:
                return None
        await self.db.execute(
            update(self.model)
            .where(self.model.user_id == user_id, self.model.used_at.is_(None))
            .values(used_at=now)
        )
        code = (
            self.code_factory()
            if self.code_factory is not None
            else str(secrets.randbelow(10**self.code_length)).zfill(self.code_length)
        )
        self.db.add(
            self.model(
                user_id=user_id,
                email=normalized_email,
                code_hash=self.hash_code(code),
                expires_at=now + timedelta(minutes=self.expire_minutes),
            )
        )
        await self.db.flush()
        return code

    async def verify(self, user_id: Any, email: str, code: str) -> Any:
        record = await self._latest(user_id, email.strip().lower())
        now = self.now()
        if record is None or _aware(record.expires_at) <= now:
            if record is not None:
                record.used_at = now
            raise VerificationCodeError(f"{self.namespace}_code_invalid")
        if record.attempts >= self.max_attempts:
            record.used_at = now
            raise VerificationCodeError(f"{self.namespace}_attempts_exceeded")
        record.attempts += 1
        if not hmac.compare_digest(record.code_hash, self.hash_code(code)):
            if record.attempts >= self.max_attempts:
                record.used_at = now
            raise VerificationCodeError(f"{self.namespace}_code_invalid")
        record.used_at = now
        await self.db.flush()
        return record

    def hash_code(self, code: str) -> str:
        normalized = "".join(char for char in code.strip() if char.isdigit())
        return hmac.digest(
            self.secret_key.encode(),
            normalized.encode(),
            "sha256",
        ).hex()

    async def _latest(self, user_id: Any, email: str) -> Any | None:
        return await self.db.scalar(
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.email == email,
                self.model.used_at.is_(None),
            )
            .order_by(self.model.id.desc())
            .limit(1)
        )


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
