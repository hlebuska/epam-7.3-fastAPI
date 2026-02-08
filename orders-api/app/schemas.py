from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    refunded = "refunded"


class OrderCreate(BaseModel):
    status: OrderStatus
    amount: float = Field(gt=0)


class OrderOut(BaseModel):
    id: int
    status: OrderStatus
    amount: float
    created_at: datetime

    model_config = {"from_attributes": True}


class OrdersListResponse(BaseModel):
    items: List[OrderOut]
    total: int
    page: int
    limit: int
