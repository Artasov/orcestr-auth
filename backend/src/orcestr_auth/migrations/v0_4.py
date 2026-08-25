from __future__ import annotations

from typing import Any

import sqlalchemy as sa


def upgrade(
    op: Any,
    *,
    user_target: str,
    user_id_type: sa.types.TypeEngine,
) -> None:
    """Add OAuth 2.1 public-client grants and session bindings."""

    op.add_column(
        "identity_auth_session",
        sa.Column("oauth_client_id", sa.String(128), nullable=True),
    )
    op.add_column(
        "identity_auth_session",
        sa.Column("scope", sa.String(1024), nullable=True),
    )
    op.create_index(
        "ix_identity_auth_session_oauth_client_id",
        "identity_auth_session",
        ["oauth_client_id"],
    )

    op.create_table(
        "identity_oauth_authorization_code",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", user_id_type, nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("client_id", sa.String(128), nullable=False),
        sa.Column("redirect_uri", sa.String(2048), nullable=False),
        sa.Column("scope", sa.String(1024), server_default="", nullable=False),
        sa.Column("code_challenge", sa.String(128), nullable=False),
        sa.Column("code_challenge_method", sa.String(16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], [user_target], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(op, "identity_oauth_authorization_code", "user_id")
    _index(op, "identity_oauth_authorization_code", "client_id")
    _index(op, "identity_oauth_authorization_code", "expires_at")
    _index(op, "identity_oauth_authorization_code", "used_at")
    op.create_index(
        "ix_identity_oauth_authorization_code_code_hash",
        "identity_oauth_authorization_code",
        ["code_hash"],
        unique=True,
    )


def downgrade(op: Any) -> None:
    op.drop_table("identity_oauth_authorization_code")
    op.drop_index(
        "ix_identity_auth_session_oauth_client_id",
        table_name="identity_auth_session",
    )
    op.drop_column("identity_auth_session", "scope")
    op.drop_column("identity_auth_session", "oauth_client_id")


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
