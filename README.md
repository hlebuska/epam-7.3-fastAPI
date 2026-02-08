# Orders Management API

A REST API for managing orders with pagination and filtering, built with FastAPI + SQLAlchemy 2.0 + SQLite.

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.0
- SQLite
- Pytest + pytest-cov

## Project Structure

```text
.
├── orders-api/
│   └── app/
│       ├── __init__.py
│       ├── crud.py
│       ├── db.py
│       ├── main.py
│       ├── models.py
│       ├── schemas.py
│       └── seed.py
├── tests/
│   └── test_orders.py
├── requirements.txt
└── README.md
```

## Setup Guide

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Run the API.
5. Seed sample data (optional).

## Installation Instructions

From project root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run the API

From project root:

```bash
uvicorn orders-api.app.main:app --reload
```

Swagger UI:

- http://127.0.0.1:8000/docs

## Seed 50 Sample Orders

Run from `orders-api/` directory:

```bash
cd orders-api
python -m app.seed
```

This creates tables (if missing) and inserts 50 sample orders with varied status, amount, and created dates across the last 60 days.

## API Endpoint Specifications

### 1. Create Order

- Method: `POST`
- Path: `/orders`
- Description: Creates a new order.

Request body:

```json
{
  "status": "pending",
  "amount": 99.5
}
```

Validation:

- `status`: one of `pending | processing | paid | shipped | delivered | cancelled | refunded`
- `amount`: must be `> 0`

Success response (`200`):

```json
{
  "id": 1,
  "status": "pending",
  "amount": 99.5,
  "created_at": "2026-02-08T12:00:00"
}
```

### 2. List Orders

- Method: `GET`
- Path: `/orders`
- Description: Returns paginated orders with optional filters.

Query params:

- `page` (default `1`, min `1`)
- `limit` (default `10`, min `1`)
- `status` (optional)
- `min_amount` (optional)
- `max_amount` (optional)
- `start_date` (optional, ISO datetime)
- `end_date` (optional, ISO datetime)

Success response (`200`):

```json
{
  "items": [
    {
      "id": 1,
      "status": "pending",
      "amount": 99.5,
      "created_at": "2026-02-08T12:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

## Usage Examples

### Create an order

```bash
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"status":"paid","amount":120.75}'
```

### Get first page (default)

```bash
curl "http://127.0.0.1:8000/orders"
```

### Get page 2 with limit 5

```bash
curl "http://127.0.0.1:8000/orders?page=2&limit=5"
```

### Filter by status + amount range

```bash
curl "http://127.0.0.1:8000/orders?status=paid&min_amount=50&max_amount=500"
```

### Filter by date range

```bash
curl "http://127.0.0.1:8000/orders?start_date=2026-01-01T00:00:00&end_date=2026-02-01T23:59:59"
```

## Running Tests

From project root:

```bash
pytest -q tests/test_orders.py
```

## Coverage

From project root:

```bash
pytest --cov=orders-api/app --cov-report=term-missing tests/test_orders.py
```

Current coverage target: `80%+`.
