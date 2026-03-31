from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.schema import ClickwrapAcceptanceCreate, ClickwrapAcceptanceRecord
from internal.clickwrap_store import get_acceptance, insert_acceptance
from internal.db import get_db
from internal.product_store import get_product

client_clickwrap_router = APIRouter(prefix="/clickwrap", tags=["v1-client-clickwrap"])


@client_clickwrap_router.post(
    "/acceptances",
    response_model=ClickwrapAcceptanceRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_clickwrap_acceptance(
    payload: ClickwrapAcceptanceCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ClickwrapAcceptanceRecord:
    if payload.product_id is not None:
        existing_product = get_product(db, str(payload.product_id))
        if existing_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found for provided product_id.",
            )
    stored = insert_acceptance(
        db,
        {
            **payload.model_dump(),
            "ip_address": request.client.host if request.client is not None else None,
            "user_agent": request.headers.get("user-agent"),
        },
    )
    return ClickwrapAcceptanceRecord.model_validate(stored)


@client_clickwrap_router.get(
    "/acceptances/{acceptance_id}",
    response_model=ClickwrapAcceptanceRecord,
)
def get_clickwrap_acceptance(
    acceptance_id: UUID,
    db: Session = Depends(get_db),
) -> ClickwrapAcceptanceRecord:
    stored = get_acceptance(db, str(acceptance_id))
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clickwrap acceptance not found.",
        )
    return ClickwrapAcceptanceRecord.model_validate(stored)
