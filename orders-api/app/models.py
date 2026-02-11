from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from .db import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_created_at_id", "created_at", "id"),
        Index("ix_orders_amount", "amount"),
    )

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(
        DateTime,
        index=True,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )
