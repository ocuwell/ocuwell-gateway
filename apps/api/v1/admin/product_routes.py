from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.schema import (
    ProductAmend,
    ProductCreate,
    ProductInstallerCreate,
    ProductInstallerRecord,
    ProductRecord,
)
from internal.db import get_db
from internal.product_store import (
    amend_product,
    create_product,
    create_product_installer,
    get_product,
    list_product_installers,
    list_products,
)

admin_product_router = APIRouter(prefix="/products", tags=["v1-admin-products"])


@admin_product_router.post("", response_model=ProductRecord, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(
    payload: ProductCreate,
    db: Session = Depends(get_db),
) -> ProductRecord:
    created = create_product(db, payload.product_name)
    return ProductRecord.model_validate(created)


@admin_product_router.get("", response_model=list[ProductRecord])
def list_products_endpoint(db: Session = Depends(get_db)) -> list[ProductRecord]:
    records = list_products(db)
    return [ProductRecord.model_validate(record) for record in records]


@admin_product_router.patch("/{product_id}", response_model=ProductRecord)
def amend_product_endpoint(
    product_id: UUID,
    payload: ProductAmend,
    db: Session = Depends(get_db),
) -> ProductRecord:
    amended = amend_product(
        db,
        str(product_id),
        product_name=payload.product_name,
    )
    if amended is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return ProductRecord.model_validate(amended)


@admin_product_router.post(
    "/{product_id}/installers",
    response_model=ProductInstallerRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_product_installer_endpoint(
    product_id: UUID,
    payload: ProductInstallerCreate,
    db: Session = Depends(get_db),
) -> ProductInstallerRecord:
    existing_product = get_product(db, str(product_id))
    if existing_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    installer = create_product_installer(db, str(product_id), payload.model_dump())
    return ProductInstallerRecord.model_validate(installer)


@admin_product_router.get("/{product_id}/installers", response_model=list[ProductInstallerRecord])
def list_product_installers_endpoint(
    product_id: UUID,
    platform: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ProductInstallerRecord]:
    existing_product = get_product(db, str(product_id))
    if existing_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    installers = list_product_installers(db, str(product_id), platform)
    return [ProductInstallerRecord.model_validate(installer) for installer in installers]
