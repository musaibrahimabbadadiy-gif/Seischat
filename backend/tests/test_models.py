"""Tests for user and authentication-session database models."""

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DatabaseSession

from app.database.base import Base
from app.models import Session, User


@pytest.fixture
def db_session() -> Iterator[DatabaseSession]:
    """Provide an isolated in-memory database for each model test."""

    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with DatabaseSession(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_user_creation_sets_id_and_database_timestamps(
    db_session: DatabaseSession,
) -> None:
    user = User(username="ada", password_hash="argon2id-hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.username == "ada"
    assert user.password_hash == "argon2id-hash"
    assert user.created_at is not None
    assert user.updated_at is not None


def test_username_must_be_unique(db_session: DatabaseSession) -> None:
    db_session.add_all(
        [
            User(username="ada", password_hash="hash-one"),
            User(username="ada", password_hash="hash-two"),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_session_belongs_to_user_and_stores_expiration(
    db_session: DatabaseSession,
) -> None:
    user = User(username="ada", password_hash="argon2id-hash")
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    session = Session(token_hash="credential-hash", expires_at=expires_at, user=user)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    assert session.user is user
    assert session in user.sessions
    assert session.user_id == user.id
    assert session.expires_at.replace(tzinfo=timezone.utc) == expires_at
    assert session.created_at is not None


def test_session_can_be_revoked(db_session: DatabaseSession) -> None:
    user = User(username="ada", password_hash="argon2id-hash")
    session = Session(
        token_hash="credential-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        user=user,
    )
    db_session.add(session)
    db_session.commit()

    revoked_at = datetime.now(timezone.utc)
    session.revoked_at = revoked_at
    db_session.commit()
    db_session.refresh(session)

    assert session.revoked_at == revoked_at.replace(tzinfo=None)


def test_session_token_hash_must_be_unique(db_session: DatabaseSession) -> None:
    user = User(username="ada", password_hash="argon2id-hash")
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.add_all(
        [
            Session(token_hash="same-hash", expires_at=expires_at, user=user),
            Session(token_hash="same-hash", expires_at=expires_at, user=user),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_session_requires_an_existing_user(db_session: DatabaseSession) -> None:
    db_session.add(
        Session(
            user_id=uuid.uuid4(),
            token_hash="credential-hash",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_model_timestamps_use_timezone_aware_database_types() -> None:
    for model in (User, Session):
        for column in model.__table__.columns:
            if column.name.endswith("_at"):
                assert column.type.timezone is True
