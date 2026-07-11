from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Callable
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import AuthConfig
from ..contracts import AuthTokens
from ..ports import UserRepository
from ..sqlalchemy import AuthModelSet
from ..tokens import TokenCodec


class AuthSessionError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AuthSessionService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        models: AuthModelSet,
        users: UserRepository,
        config: AuthConfig,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.db = session
        self.models = models
        self.users = users
        self.config = config
        self.codec = TokenCodec(config)
        self.now = now

    @staticmethod
    def token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def new_refresh_token() -> str:
        return secrets.token_urlsafe(48)

    async def create(
        self,
        user: Any,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthTokens:
        now = self.now()
        expires_at = now + timedelta(days=self.config.refresh_token_days)
        session_id = str(uuid4())
        raw_refresh = self.new_refresh_token()
        self.db.add(
            self.models.session(
                id=session_id,
                user_id=self.users.user_id(user),
                expires_at=expires_at,
                last_used_at=now,
                ip_address=(ip_address or "")[:64] or None,
                user_agent=(user_agent or "")[:512] or None,
            )
        )
        await self.db.flush()
        self.db.add(
            self.models.refresh_token(
                id=str(uuid4()),
                session_id=session_id,
                token_hash=self.token_hash(raw_refresh),
                expires_at=expires_at,
            )
        )
        await self.db.flush()
        return AuthTokens(
            access_token=self.codec.create_access_token(
                self.users.user_id(user), session_id=session_id
            ),
            refresh_token=raw_refresh,
        )

    async def rotate(
        self,
        raw_refresh: str | None,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthTokens:
        if not raw_refresh:
            raise AuthSessionError("refresh_token_missing")
        token = await self.db.scalar(
            select(self.models.refresh_token)
            .where(
                self.models.refresh_token.token_hash == self.token_hash(raw_refresh)
            )
            .with_for_update()
        )
        if token is None:
            raise AuthSessionError("refresh_token_invalid")
        auth_session = await self.db.scalar(
            select(self.models.session)
            .where(self.models.session.id == token.session_id)
            .with_for_update()
        )
        if auth_session is None:
            raise AuthSessionError("refresh_token_invalid")
        now = self.now()
        if token.used_at is not None or token.revoked_at is not None:
            await self._revoke_session(auth_session.id, now)
            await self.db.commit()
            raise AuthSessionError("refresh_token_reused")
        if (
            auth_session.revoked_at is not None
            or aware_utc(auth_session.expires_at) <= now
            or aware_utc(token.expires_at) <= now
        ):
            await self._revoke_session(auth_session.id, now)
            await self.db.commit()
            raise AuthSessionError("refresh_token_expired")
        user = await self.users.get_by_id(auth_session.user_id)
        if user is None or not self.users.is_active(user):
            await self._revoke_session(auth_session.id, now)
            await self.db.commit()
            raise AuthSessionError("user_inactive")
        token.used_at = now
        auth_session.last_used_at = now
        if ip_address:
            auth_session.ip_address = ip_address[:64]
        if user_agent:
            auth_session.user_agent = user_agent[:512]
        next_refresh = self.new_refresh_token()
        self.db.add(
            self.models.refresh_token(
                id=str(uuid4()),
                session_id=auth_session.id,
                token_hash=self.token_hash(next_refresh),
                expires_at=auth_session.expires_at,
            )
        )
        await self.db.flush()
        return AuthTokens(
            access_token=self.codec.create_access_token(
                self.users.user_id(user), session_id=auth_session.id
            ),
            refresh_token=next_refresh,
        )

    async def revoke(
        self,
        raw_refresh: str | None,
        *,
        session_id: str | None = None,
        commit: bool = True,
    ) -> None:
        resolved = session_id
        if raw_refresh:
            found = await self.db.scalar(
                select(self.models.refresh_token.session_id).where(
                    self.models.refresh_token.token_hash
                    == self.token_hash(raw_refresh)
                )
            )
            resolved = str(found) if found else resolved
        if resolved:
            await self._revoke_session(resolved, self.now())
        if commit:
            await self.db.commit()

    async def revoke_user_sessions(self, user_id: Any) -> None:
        session_ids = list(
            await self.db.scalars(
                select(self.models.session.id).where(
                    self.models.session.user_id == user_id,
                    self.models.session.revoked_at.is_(None),
                )
            )
        )
        now = self.now()
        for session_id in session_ids:
            await self._revoke_session(str(session_id), now)

    async def _revoke_session(self, session_id: str, revoked_at: datetime) -> None:
        await self.db.execute(
            update(self.models.session)
            .where(
                self.models.session.id == session_id,
                self.models.session.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self.db.execute(
            update(self.models.refresh_token)
            .where(
                self.models.refresh_token.session_id == session_id,
                self.models.refresh_token.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
