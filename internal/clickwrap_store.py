from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from internal.models import ClickwrapAcceptance


def insert_acceptance(db: Session, payload: dict[str, Any]) -> ClickwrapAcceptance:
    acceptance_id = str(uuid4())
    now_utc = datetime.now(timezone.utc)
    product_id = payload.get("product_id")
    record = ClickwrapAcceptance(
        id=acceptance_id,
        agreement_id=payload["agreement_id"],
        agreement_version=payload["agreement_version"],
        decision=payload["decision"],
        product_id=str(product_id) if product_id is not None else None,
        product_version=payload.get("product_version"),
        accepted_by=payload["accepted_by"],
        accepted_at=payload["accepted_at"],
        ip_address=payload.get("ip_address"),
        user_agent=payload.get("user_agent"),
        context=payload.get("context", {}),
        recorded_at=now_utc,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_acceptance(db: Session, acceptance_id: str) -> ClickwrapAcceptance | None:
    return db.get(ClickwrapAcceptance, acceptance_id)
