from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import registry as Registry


@dataclass(frozen=True, slots=True)
class AuthTableNames:
    oauth_account: str = "identity_oauth_account"
    email_verification: str = "identity_email_verification_code"
    password_reset: str = "identity_password_reset_code"
    session: str = "identity_auth_session"
    refresh_token: str = "identity_auth_refresh_token"
    websocket_ticket: str = "identity_websocket_ticket"


@dataclass(frozen=True, slots=True)
class AuthModelSet:
    oauth_account: type[Any]
    email_verification: type[Any]
    password_reset: type[Any]
    session: type[Any]
    refresh_token: type[Any]
    websocket_ticket: type[Any]


def _timestamps() -> tuple[Any, Any]:
    return (
        Column(
            "created_at",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        Column(
            "updated_at",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )


def create_auth_models(
    *,
    registry: Registry,
    user_model: type[Any],
    names: AuthTableNames = AuthTableNames(),
) -> AuthModelSet:
    """Map auth tables into the consumer registry with real user foreign keys."""

    metadata = registry.metadata
    user_table = user_model.__table__
    primary_keys = list(user_table.primary_key.columns)
    if len(primary_keys) != 1:
        raise ValueError("The auth user model must have exactly one primary key.")
    user_pk = primary_keys[0]
    user_target = f"{user_table.fullname}.{user_pk.name}"

    oauth_table = Table(
        names.oauth_account,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column(
            "user_id",
            user_pk.type.copy(),
            ForeignKey(user_target, ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        Column("provider", String(32), nullable=False, index=True),
        Column("provider_user_id", String(255), nullable=False),
        Column("email", String(255), nullable=True),
        *_timestamps(),
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_identity_oauth_account_provider_user",
        ),
    )
    verification_table = _code_table(
        metadata, names.email_verification, user_pk, user_target
    )
    password_reset_table = _code_table(
        metadata, names.password_reset, user_pk, user_target
    )
    session_table = Table(
        names.session,
        metadata,
        Column("id", String(36), primary_key=True),
        Column(
            "user_id",
            user_pk.type.copy(),
            ForeignKey(user_target, ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
        Column("last_used_at", DateTime(timezone=True), nullable=False),
        Column("revoked_at", DateTime(timezone=True), nullable=True, index=True),
        Column("ip_address", String(64), nullable=True),
        Column("user_agent", String(512), nullable=True),
        *_timestamps(),
    )
    refresh_table = Table(
        names.refresh_token,
        metadata,
        Column("id", String(36), primary_key=True),
        Column(
            "session_id",
            String(36),
            ForeignKey(f"{names.session}.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        Column("token_hash", String(64), nullable=False, unique=True, index=True),
        Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
        Column("used_at", DateTime(timezone=True), nullable=True),
        Column("revoked_at", DateTime(timezone=True), nullable=True, index=True),
        *_timestamps(),
    )
    ticket_table = Table(
        names.websocket_ticket,
        metadata,
        Column("id", String(32), primary_key=True),
        Column(
            "user_id",
            user_pk.type.copy(),
            ForeignKey(user_target, ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
        Column("used_at", DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )

    Index(
        "ix_identity_auth_session_user_revoked",
        session_table.c.user_id,
        session_table.c.revoked_at,
    )

    return AuthModelSet(
        oauth_account=_map(registry, "OAuthAccountORM", oauth_table),
        email_verification=_map(
            registry, "EmailVerificationCodeORM", verification_table
        ),
        password_reset=_map(registry, "PasswordResetCodeORM", password_reset_table),
        session=_map(registry, "AuthSessionORM", session_table),
        refresh_token=_map(registry, "AuthRefreshTokenORM", refresh_table),
        websocket_ticket=_map(registry, "WebSocketTicketORM", ticket_table),
    )


def _code_table(metadata: Any, name: str, user_pk: Any, user_target: str) -> Table:
    return Table(
        name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column(
            "user_id",
            user_pk.type.copy(),
            ForeignKey(user_target, ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        Column("email", String(255), nullable=False, index=True),
        Column("code_hash", String(128), nullable=False),
        Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
        Column("used_at", DateTime(timezone=True), nullable=True),
        Column("attempts", Integer, default=0, nullable=False),
        *_timestamps(),
    )


def _map(registry: Registry, name: str, table: Table) -> type[Any]:
    model = type(name, (), {"__module__": "orcestr_auth.sqlalchemy.models"})
    registry.map_imperatively(model, table)
    return model
