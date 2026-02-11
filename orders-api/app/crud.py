from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .models import Order
from .schemas import OrderCreate, OrderStatus

ALLOWED_ORDER_STATUSES = tuple(status.value for status in OrderStatus)


class DatabaseOperationError(Exception):
    pass


def create_order(db: Session, order_in: OrderCreate) -> Order:
    order = Order(status=order_in.status.value, amount=order_in.amount)
    db.add(order)
    try:
        db.commit()
        db.refresh(order)
    except SQLAlchemyError as exc:
        db.rollback()
        raise DatabaseOperationError("failed to create order") from exc
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

    filters = [Order.status.in_(ALLOWED_ORDER_STATUSES)]
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
        select(Order, func.count(Order.id).over().label("total_count"))
        .where(*filters)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    try:
        rows = db.execute(items_stmt).all()
    except SQLAlchemyError as exc:
        raise DatabaseOperationError("failed to list orders") from exc

    items = [row[0] for row in rows]
    if rows:
        total = int(rows[0][1])
    else:
        total_stmt = select(func.count(Order.id)).where(*filters)
        try:
            total = db.execute(total_stmt).scalar_one()
        except SQLAlchemyError as exc:
            raise DatabaseOperationError("failed to count orders") from exc

    return {"items": items, "total": total}
