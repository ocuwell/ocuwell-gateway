from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from internal.models import Product, ProductInstaller


def create_product(db: Session, product_name: str) -> Product:
    now_utc = datetime.now(timezone.utc)
    product = Product(
        id=str(uuid4()),
        product_name=product_name,
        created_at=now_utc,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session) -> list[Product]:
    stmt = select(Product).order_by(Product.created_at.desc())
    return list(db.scalars(stmt).all())


def get_product(db: Session, product_id: str) -> Product | None:
    return db.get(Product, product_id)


def amend_product(
    db: Session,
    product_id: str,
    product_name: str | None = None,
) -> Product | None:
    product = db.get(Product, product_id)
    if product is None:
        return None

    if product_name is not None:
        product.product_name = product_name

    db.commit()
    db.refresh(product)
    return product


def create_product_installer(
    db: Session,
    product_id: str,
    payload: dict,
) -> ProductInstaller:
    if payload.get("is_latest"):
        existing_latest_stmt = select(ProductInstaller).where(
            ProductInstaller.product_id == product_id,
            ProductInstaller.platform == payload["platform"],
            ProductInstaller.is_latest.is_(True),
        )
        for existing in db.scalars(existing_latest_stmt):
            existing.is_latest = False

    now_utc = datetime.now(timezone.utc)
    installer = ProductInstaller(
        id=str(uuid4()),
        product_id=product_id,
        version=payload["version"],
        platform=payload["platform"],
        blob_url=payload["blob_url"],
        file_name=payload["file_name"],
        checksum_sha256=payload.get("checksum_sha256"),
        file_size_bytes=payload.get("file_size_bytes"),
        is_latest=payload.get("is_latest", False),
        created_at=now_utc,
    )
    db.add(installer)
    db.commit()
    db.refresh(installer)
    return installer


def list_product_installers(
    db: Session,
    product_id: str,
    platform: str | None = None,
) -> list[ProductInstaller]:
    stmt = select(ProductInstaller).where(ProductInstaller.product_id == product_id)
    if platform:
        stmt = stmt.where(ProductInstaller.platform == platform)
    stmt = stmt.order_by(ProductInstaller.created_at.desc())
    return list(db.scalars(stmt).all())
