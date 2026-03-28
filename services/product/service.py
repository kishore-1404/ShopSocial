from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models import Category, Product, ProductPost


def list_products(db: Session) -> list[Product]:
    return db.query(Product).all()


def list_categories(db: Session) -> list[Category]:
    return db.query(Category).all()


def list_posts(db: Session) -> list[ProductPost]:
    return db.query(ProductPost).all()


def search_products(
    db: Session,
    name: Optional[str] = None,
    category_id: Optional[int] = None,
) -> list[Product]:
    query = db.query(Product)
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    return query.all()