from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "orders-api"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app import seed  # noqa: E402
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Order  # noqa: E402


STATUSES = ["pending", "processing", "paid", "shipped", "delivered"]


@pytest.fixture()
def client_and_session(tmp_path):
    db_path = tmp_path / "test_orders.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, TestingSessionLocal

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture()
def seeded_client(client_and_session):
    client, TestingSessionLocal = client_and_session
    now = datetime(2026, 2, 8, 12, 0, 0)
    session = TestingSessionLocal()
    try:
        orders = []
        for i in range(20):
            orders.append(
                Order(
                    status=STATUSES[i % len(STATUSES)],
                    amount=float((i + 1) * 10),
                    created_at=now - timedelta(days=i * 3),
                )
            )
        session.add_all(orders)
        session.commit()
    finally:
        session.close()
    return client


def test_post_creates_order_valid(client_and_session):
    client, _ = client_and_session
    response = client.post("/orders", json={"status": "pending", "amount": 99.5})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] > 0
    assert data["status"] == "pending"
    assert data["amount"] == 99.5
    assert "created_at" in data


def test_post_rejects_invalid_amount_non_positive(client_and_session):
    client, _ = client_and_session
    response = client.post("/orders", json={"status": "pending", "amount": 0})
    assert response.status_code == 422


def test_post_rejects_invalid_status(client_and_session):
    client, _ = client_and_session
    response = client.post("/orders", json={"status": "unknown", "amount": 20})
    assert response.status_code == 422


def test_get_default_returns_limit_and_total(seeded_client):
    response = seeded_client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 20
    assert data["limit"] == 10
    assert data["page"] == 1


def test_get_page_two_differs_from_page_one(seeded_client):
    page1 = seeded_client.get("/orders?page=1&limit=10").json()
    page2 = seeded_client.get("/orders?page=2&limit=10").json()
    ids_page1 = [item["id"] for item in page1["items"]]
    ids_page2 = [item["id"] for item in page2["items"]]
    assert ids_page1 != ids_page2
    assert len(set(ids_page1).intersection(set(ids_page2))) == 0


def test_get_limit_five_returns_five(seeded_client):
    response = seeded_client.get("/orders?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["limit"] == 5


def test_get_page_beyond_range_empty_items_with_total(seeded_client):
    response = seeded_client.get("/orders?page=999&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 20


def test_filter_status_only_returns_that_status(seeded_client):
    response = seeded_client.get("/orders?status=pending&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(item["status"] == "pending" for item in data["items"])


def test_filter_min_amount(seeded_client):
    response = seeded_client.get("/orders?min_amount=150&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(item["amount"] >= 150 for item in data["items"])


def test_filter_max_amount(seeded_client):
    response = seeded_client.get("/orders?max_amount=80&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(item["amount"] <= 80 for item in data["items"])


def test_filter_min_max_amount_range(seeded_client):
    response = seeded_client.get("/orders?min_amount=70&max_amount=130&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(70 <= item["amount"] <= 130 for item in data["items"])


def test_filter_start_date(seeded_client):
    start_dt = datetime(2026, 1, 15, 0, 0, 0)
    response = seeded_client.get(f"/orders?start_date={start_dt.isoformat()}&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(datetime.fromisoformat(item["created_at"]) >= start_dt for item in data["items"])


def test_filter_end_date(seeded_client):
    end_dt = datetime(2025, 12, 31, 23, 59, 59)
    response = seeded_client.get(f"/orders?end_date={end_dt.isoformat()}&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(datetime.fromisoformat(item["created_at"]) <= end_dt for item in data["items"])


def test_filter_date_range(seeded_client):
    start_dt = datetime(2026, 1, 1, 0, 0, 0)
    end_dt = datetime(2026, 1, 31, 23, 59, 59)
    response = seeded_client.get(
        f"/orders?start_date={start_dt.isoformat()}&end_date={end_dt.isoformat()}&limit=50"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(
        start_dt <= datetime.fromisoformat(item["created_at"]) <= end_dt for item in data["items"]
    )


def test_filter_combined_status_amount_and_date_range(seeded_client):
    start_dt = datetime(2025, 12, 20, 0, 0, 0)
    end_dt = datetime(2026, 2, 8, 23, 59, 59)
    response = seeded_client.get(
        f"/orders?status=paid&min_amount=10&start_date={start_dt.isoformat()}&end_date={end_dt.isoformat()}&limit=50"
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "paid" for item in data["items"])
    assert all(item["amount"] >= 10 for item in data["items"])
    assert all(
        start_dt <= datetime.fromisoformat(item["created_at"]) <= end_dt
        for item in data["items"]
    )


def test_edge_page_zero_rejected(seeded_client):
    response = seeded_client.get("/orders?page=0")
    assert response.status_code == 422


def test_edge_limit_zero_rejected(seeded_client):
    response = seeded_client.get("/orders?limit=0")
    assert response.status_code == 422


def test_edge_min_amount_greater_than_max_returns_empty(seeded_client):
    response = seeded_client.get("/orders?min_amount=300&max_amount=100&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_seed_orders_inserts_expected_data(monkeypatch, tmp_path):
    db_path = tmp_path / "seed_test.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    monkeypatch.setattr(seed, "engine", test_engine)
    monkeypatch.setattr(seed, "SessionLocal", TestingSessionLocal)

    inserted = seed.seed_orders(total=50)
    assert inserted == 50

    session = TestingSessionLocal()
    try:
        orders = session.execute(select(Order)).scalars().all()
        assert len(orders) == 50

        statuses = {
            "pending",
            "processing",
            "paid",
            "shipped",
            "delivered",
            "cancelled",
            "refunded",
        }
        now = datetime.now(UTC).replace(tzinfo=None)
        oldest_allowed = now - timedelta(days=60)

        for order in orders:
            assert order.status in statuses
            assert 10.0 <= order.amount <= 1000.0
            assert oldest_allowed <= order.created_at <= now
    finally:
        session.close()
        test_engine.dispose()
