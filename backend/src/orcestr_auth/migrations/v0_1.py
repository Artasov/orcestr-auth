from __future__ import annotations

from typing import Any

import sqlalchemy as sa


AUTH_TABLES = (
    "identity_auth_refresh_token",
    "identity_auth_session",
    "identity_websocket_ticket",
    "identity_password_reset_code",
    "identity_email_verification_code",
    "identity_oauth_account",
)


def upgrade(op: Any, *, user_target: str, user_id_type: sa.types.TypeEngine) -> None:
    """Create the immutable v0.1 auth schema in a consumer migration."""

    op.create_table(
        "identity_oauth_account",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", user_id_type, nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], [user_target], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_identity_oauth_account_provider_user",
        ),
    )
    _index(op, "identity_oauth_account", "provider")
    _index(op, "identity_oauth_account", "user_id")

    _create_code_table(
        op,
        "identity_email_verification_code",
        user_target,
        user_id_type,
    )
    _create_code_table(
        op,
        "identity_password_reset_code",
        user_target,
        user_id_type,
    )

    op.create_table(
        "identity_auth_session",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", user_id_type, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], [user_target], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(op, "identity_auth_session", "user_id")
    _index(op, "identity_auth_session", "expires_at")
    _index(op, "identity_auth_session", "revoked_at")
    op.create_index(
        "ix_identity_auth_session_user_revoked",
        "identity_auth_session",
        ["user_id", "revoked_at"],
    )

    op.create_table(
        "identity_auth_refresh_token",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["identity_auth_session.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(op, "identity_auth_refresh_token", "session_id")
    _index(op, "identity_auth_refresh_token", "expires_at")
    _index(op, "identity_auth_refresh_token", "revoked_at")
    op.create_index(
        "ix_identity_auth_refresh_token_token_hash",
        "identity_auth_refresh_token",
        ["token_hash"],
        unique=True,
    )

    op.create_table(
        "identity_websocket_ticket",
        sa.Column("id", sa.String(32), nullable=False),
        sa.Column("user_id", user_id_type, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], [user_target], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(op, "identity_websocket_ticket", "user_id")
    _index(op, "identity_websocket_ticket", "expires_at")


def downgrade(op: Any) -> None:
    for table in AUTH_TABLES:
        op.drop_table(table)


def _create_code_table(
    op: Any,
    table: str,
    user_target: str,
    user_id_type: sa.types.TypeEngine,
) -> None:
    op.create_table(
        table,
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", user_id_type, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], [user_target], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(op, table, "user_id")
    _index(op, table, "email")
    _index(op, table, "expires_at")


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def _index(op: Any, table: str, column: str) -> None:
    op.create_index(f"ix_{table}_{column}", table, [column])
