import pytest
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from orcestr_auth import AuthConfig, TokenPayloadError
from orcestr_auth.services import WebSocketTicketService
from orcestr_auth.sqlalchemy import create_auth_models


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "websocket_test_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


MODELS = create_auth_models(registry=Base.registry, user_model=User)


async def test_websocket_ticket_is_one_time() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(
            User(
                id=1,
                username="user",
                email="user@example.com",
                password_hash="hash",
            )
        )
        await session.flush()
        service = WebSocketTicketService(
            session,
            models=MODELS,
            config=AuthConfig(secret_key="secret"),
        )
        token = await service.issue(1)
        await session.commit()
        assert await service.consume(token) == 1
        await session.commit()
        with pytest.raises(TokenPayloadError, match="Invalid WebSocket ticket"):
            await service.consume(token)
    await engine.dispose()
