from datetime import datetime
from typing import List

from pydantic import BaseModel


class OrderCreate(BaseModel):
    status: str
    amount: float


class OrderOut(BaseModel):
    id: int
    status: str
    amount: float
    created_at: datetime

    model_config = {"from_attributes": True}


class OrdersListResponse(BaseModel):
    items: List[OrderOut]
    total: int
    page: int
    limit: int
