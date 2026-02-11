from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session

from . import crud, schemas
from .db import Base, engine
from .db import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)


def _to_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


@app.post("/orders", response_model=schemas.OrderOut)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_order(db=db, order_in=order_in)
    except crud.DatabaseOperationError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create order",
        ) from exc


@app.get("/orders", response_model=schemas.OrdersListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[schemas.OrderStatus] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_amount must be less than or equal to max_amount",
        )

    normalized_start_date = _to_naive_utc(start_date)
    normalized_end_date = _to_naive_utc(end_date)
    if (
        normalized_start_date is not None
        and normalized_end_date is not None
        and normalized_start_date > normalized_end_date
    ):
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start_date must be less than or equal to end_date",
        )

    try:
        result = crud.list_orders(
            db=db,
            page=page,
            limit=limit,
            status=status.value if status is not None else None,
            min_amount=min_amount,
            max_amount=max_amount,
            start_date=normalized_start_date,
            end_date=normalized_end_date,
        )
    except crud.DatabaseOperationError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to list orders",
        ) from exc
    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "limit": limit,
    }
