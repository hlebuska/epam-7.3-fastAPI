from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from .db import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(
        DateTime,
        index=True,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )
