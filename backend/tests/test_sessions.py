from datetime import UTC, datetime

import pytest
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from orcestr_auth import AuthConfig
from orcestr_auth.services.sessions import AuthSessionError, AuthSessionService
from orcestr_auth.sqlalchemy import (
    SqlAlchemyUserRepository,
    UserFieldMap,
    create_auth_models,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "session_test_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


FIELDS = UserFieldMap(
    id=User.id,
    username=User.username,
    email=User.email,
    password_hash=User.password_hash,
    is_active=User.is_active,
)
MODELS = create_auth_models(registry=Base.registry, user_model=User)


async def test_refresh_rotation_and_replay_revoke_session() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user = User(
            id=1,
            username="user",
            email="user@example.com",
            password_hash="hash",
            is_active=True,
        )
        session.add(user)
        await session.flush()
        service = AuthSessionService(
            session,
            models=MODELS,
            users=SqlAlchemyUserRepository(session, User, FIELDS),
            config=AuthConfig(secret_key="test-secret"),
        )
        first = await service.create(user)
        await session.commit()
        second = await service.rotate(first.refresh_token)
        await session.commit()
        assert second.refresh_token != first.refresh_token
        with pytest.raises(AuthSessionError, match="refresh_token_reused"):
            await service.rotate(first.refresh_token)
        decoded = service.codec.decode(second.access_token, "access")
        auth_session = await session.get(MODELS.session, decoded["sid"])
        assert auth_session.revoked_at is not None
        revoked_at = auth_session.revoked_at
        if revoked_at.tzinfo is None:
            revoked_at = revoked_at.replace(tzinfo=UTC)
        assert revoked_at <= datetime.now(UTC)
    await engine.dispose()
