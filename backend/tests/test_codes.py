from sqlalchemy import Boolean, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import pytest

from orcestr_auth.services.codes import VerificationCodeError, VerificationCodeService
from orcestr_auth.sqlalchemy import create_auth_models


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "code_test_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


MODELS = create_auth_models(registry=Base.registry, user_model=User)


async def test_codes_are_hashed_one_time_values() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(User(id=1, username="user", email="user@example.com", password_hash="hash"))
        await session.flush()
        service = VerificationCodeService(
            session,
            model=MODELS.password_reset,
            secret_key="secret",
            expire_minutes=15,
            code_length=6,
            max_attempts=5,
            resend_cooldown_seconds=60,
            namespace="password_reset",
            code_factory=lambda: "123456",
        )
        code = await service.issue(1, "USER@example.com")
        await session.commit()
        assert code == "123456"
        record = await service.verify(1, "user@example.com", "123456")
        assert record.code_hash != code
        assert record.used_at is not None
        with pytest.raises(VerificationCodeError, match="password_reset_code_invalid"):
            await service.verify(1, "user@example.com", "123456")
    await engine.dispose()
