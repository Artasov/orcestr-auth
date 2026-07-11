from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from orcestr_auth.sqlalchemy import create_auth_models


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "app_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool]


def test_auth_models_share_consumer_metadata_and_user_fk() -> None:
    models = create_auth_models(registry=Base.registry, user_model=User)
    assert models.session.__table__.metadata is Base.metadata
    foreign_key = next(iter(models.session.__table__.c.user_id.foreign_keys))
    assert foreign_key.target_fullname == "app_user.id"
    expected = {
        "identity_oauth_account",
        "identity_email_verification_code",
        "identity_password_reset_code",
        "identity_auth_session",
        "identity_auth_refresh_token",
        "identity_websocket_ticket",
    }
    assert expected.issubset(Base.metadata.tables)
