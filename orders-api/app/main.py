from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Query
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .db import Base, engine
from .db import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/orders", response_model=schemas.OrderOut)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    return crud.create_order(db=db, order_in=order_in)


@app.get("/orders", response_model=schemas.OrdersListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    status: Optional[schemas.OrderStatus] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    result = crud.list_orders(
        db=db,
        page=page,
        limit=limit,
        status=status.value if status is not None else None,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date,
    )
    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "limit": limit,
    }
