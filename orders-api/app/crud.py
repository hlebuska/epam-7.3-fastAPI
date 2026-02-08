from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Order
from .schemas import OrderCreate


def create_order(db: Session, order_in: OrderCreate) -> Order:
    order = Order(status=order_in.status, amount=order_in.amount)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_orders(
    db: Session,
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    filters = []
    if status is not None:
        filters.append(Order.status == status)
    if min_amount is not None:
        filters.append(Order.amount >= min_amount)
    if max_amount is not None:
        filters.append(Order.amount <= max_amount)
    if start_date is not None:
        filters.append(Order.created_at >= start_date)
    if end_date is not None:
        filters.append(Order.created_at <= end_date)

    items_stmt = (
        select(Order)
        .where(*filters)
        .order_by(Order.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    items = db.execute(items_stmt).scalars().all()

    total_stmt = select(func.count(Order.id)).where(*filters)
    total = db.execute(total_stmt).scalar_one()

    return {"items": items, "total": total}
