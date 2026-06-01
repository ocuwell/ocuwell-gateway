from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request

from apps.api.schema import ClickwrapAcceptanceCreate
from apps.api.v1.clients.clickwrap_routes import (
    create_clickwrap_acceptance,
    get_clickwrap_acceptance,
)
from internal.clickwrap_store import get_acceptance, insert_acceptance
from internal.db import Base
from internal.models import Product


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def make_request(*, ip_address: str = "127.0.0.1", user_agent: str = "test-agent") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [(b"user-agent", user_agent.encode("utf-8"))],
        "client": (ip_address, 12345),
    }
    return Request(scope)


def make_request_without_client(*, user_agent: str = "test-agent") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [(b"user-agent", user_agent.encode("utf-8"))],
    }
    return Request(scope)


def make_payload(**overrides: object) -> ClickwrapAcceptanceCreate:
    data = {
        "agreement_id": "ocuwell-eula",
        "agreement_version": "2026-03-31",
        "decision": "accept",
        "accepted_by": "user@example.com",
        "accepted_at": datetime.now(timezone.utc),
        "context": {"source": "unit-test"},
    }
    data.update(overrides)
    return ClickwrapAcceptanceCreate(**data)


def test_insert_acceptance_persists_record(db_session: Session) -> None:
    record = insert_acceptance(
        db_session,
        {
            **make_payload().model_dump(),
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent",
        },
    )

    assert record.decision == "accept"
    assert record.ip_address == "127.0.0.1"
    assert record.user_agent == "test-agent"


def test_get_acceptance_returns_none_for_unknown_id(db_session: Session) -> None:
    assert get_acceptance(db_session, str(uuid4())) is None


def test_create_accept_decision(db_session: Session) -> None:
    record = create_clickwrap_acceptance(make_payload(), make_request(), db_session)

    assert record.decision == "accept"
    assert record.ip_address == "127.0.0.1"
    assert record.user_agent == "test-agent"


def test_create_decline_decision(db_session: Session) -> None:
    record = create_clickwrap_acceptance(
        make_payload(decision="decline"),
        make_request(),
        db_session,
    )

    assert record.decision == "decline"


def test_create_with_unknown_product_returns_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as error:
        create_clickwrap_acceptance(
            make_payload(product_id=uuid4()),
            make_request(),
            db_session,
        )

    assert error.value.status_code == 404


def test_create_with_known_product_succeeds(db_session: Session) -> None:
    product = Product(
        id=str(uuid4()),
        product_name="Ocuwell Desktop",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(product)
    db_session.commit()

    record = create_clickwrap_acceptance(
        make_payload(product_id=product.id),
        make_request(),
        db_session,
    )

    assert str(record.product_id) == product.id


def test_create_without_request_client_stores_no_ip(db_session: Session) -> None:
    record = create_clickwrap_acceptance(
        make_payload(),
        make_request_without_client(),
        db_session,
    )

    assert record.ip_address is None
    assert record.user_agent == "test-agent"


def test_get_unknown_acceptance_returns_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as error:
        get_clickwrap_acceptance(uuid4(), db_session)

    assert error.value.status_code == 404


def test_create_then_get_round_trip(db_session: Session) -> None:
    created = create_clickwrap_acceptance(make_payload(), make_request(), db_session)

    fetched = get_clickwrap_acceptance(created.id, db_session)

    assert fetched.id == created.id
    assert fetched.agreement_id == "ocuwell-eula"
    assert fetched.context == {"source": "unit-test"}
