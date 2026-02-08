from datetime import UTC, datetime, timedelta
import random

from .db import Base, SessionLocal, engine
from .models import Order


def seed_orders(total: int = 50) -> int:
    Base.metadata.create_all(bind=engine)

    rng = random.Random(42)
    now = datetime.now(UTC).replace(tzinfo=None)
    statuses = [
        "pending",
        "processing",
        "paid",
        "shipped",
        "delivered",
        "cancelled",
        "refunded",
    ]

    session = SessionLocal()
    try:
        orders = []
        for _ in range(total):
            days_ago = rng.randint(0, 59)
            minutes_ago = rng.randint(0, 23 * 60 + 59)
            created_at = now - timedelta(days=days_ago, minutes=minutes_ago)

            orders.append(
                Order(
                    status=rng.choice(statuses),
                    amount=round(rng.uniform(10.0, 1000.0), 2),
                    created_at=created_at,
                )
            )

        session.add_all(orders)
        session.commit()
        return len(orders)
    finally:
        session.close()


if __name__ == "__main__":
    inserted = seed_orders(50)
    print(f"Inserted {inserted} sample orders.")
