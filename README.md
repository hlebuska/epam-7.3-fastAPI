# Orders Management API

A REST API for managing orders with pagination and filtering, built with FastAPI + SQLAlchemy 2.0 + SQLite.

Full API request/response documentation with examples: `API_DOCUMENTATION.md`

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
- `limit` (default `10`, min `1`, max `100`)
- `status` (optional; one of `pending | processing | paid | shipped | delivered | cancelled | refunded`)
- `min_amount` (optional)
- `max_amount` (optional)
- `start_date` (optional, ISO datetime)
- `end_date` (optional, ISO datetime)

Validation:

- Returns `422` when `min_amount > max_amount`
- Returns `422` when `start_date > end_date`
- Datetime filters accept ISO-8601 datetimes, including timezone offsets (for example `Z` or `+00:00`), and are normalized to UTC for comparison.

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

### Invalid range example (`422`)

```bash
curl "http://127.0.0.1:8000/orders?min_amount=300&max_amount=100"
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

Current coverage: `80%+`.

Name                         Stmts   Miss  Cover   Missing
----------------------------------------------------------
orders-api/app/__init__.py       0      0   100%
orders-api/app/crud.py          33      2    94%   30, 32
orders-api/app/db.py            12      4    67%   22-26
orders-api/app/main.py          20      0   100%
orders-api/app/models.py         9      0   100%
orders-api/app/schemas.py       26      0   100%
orders-api/app/seed.py          24      2    92%   47-48
----------------------------------------------------------
TOTAL                          124      8    94%

# Orders API Documentation

Base URL: `http://127.0.0.1:8000`

## Authentication

No authentication is required.

## Content Type

- Request body: `application/json` (for `POST /orders`)
- Response body: `application/json`

## Data Model

### Order status values

`pending`, `processing`, `paid`, `shipped`, `delivered`, `cancelled`, `refunded`

### Order object

```json
{
  "id": 1,
  "status": "pending",
  "amount": 99.5,
  "created_at": "2026-02-08T12:00:00"
}
```

## Endpoints

### POST /orders

Create a new order.

#### Request example

```bash
curl -X POST "http://127.0.0.1:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{"status":"paid","amount":120.75}'
```

```json
{
  "status": "paid",
  "amount": 120.75
}
```

#### Success response (`200`)

```json
{
  "id": 21,
  "status": "paid",
  "amount": 120.75,
  "created_at": "2026-02-11T18:30:00.000000"
}
```

#### Validation error response (`422`)

Example invalid status:

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "status"],
      "msg": "Input should be 'pending', 'processing', 'paid', 'shipped', 'delivered', 'cancelled' or 'refunded'",
      "input": "unknown"
    }
  ]
}
```

Example invalid amount (`<= 0`):

```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "amount"],
      "msg": "Input should be greater than 0",
      "input": 0,
      "ctx": {"gt": 0.0}
    }
  ]
}
```

#### Server error response (`500`)

```json
{
  "detail": "Unable to create order"
}
```

### GET /orders

Return paginated orders with optional filters.

#### Query parameters

- `page`: integer, default `1`, min `1`
- `limit`: integer, default `10`, min `1`, max `100`
- `status`: one of order status values
- `min_amount`: number
- `max_amount`: number
- `start_date`: ISO-8601 datetime (timezone accepted)
- `end_date`: ISO-8601 datetime (timezone accepted)

#### Request examples

Default list:

```bash
curl "http://127.0.0.1:8000/orders"
```

Filtered list:

```bash
curl "http://127.0.0.1:8000/orders?status=paid&min_amount=50&max_amount=500&start_date=2026-01-01T00:00:00Z&end_date=2026-02-01T23:59:59Z&page=1&limit=5"
```

#### Success response (`200`)

```json
{
  "items": [
    {
      "id": 12,
      "status": "paid",
      "amount": 120.75,
      "created_at": "2026-01-30T09:15:00"
    },
    {
      "id": 7,
      "status": "paid",
      "amount": 80.0,
      "created_at": "2026-01-21T16:05:00"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 5
}
```

#### Validation error response (`422`)

Example invalid amount range:

```json
{
  "detail": "min_amount must be less than or equal to max_amount"
}
```

Example invalid date range:

```json
{
  "detail": "start_date must be less than or equal to end_date"
}
```

Example invalid page type:

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["query", "page"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
    }
  ]
}
```

#### Server error response (`500`)

```json
{
  "detail": "Unable to list orders"
}
```

## Notes

- Orders are sorted by `created_at DESC`, then `id DESC`.
- Datetime filters with timezone offsets are normalized to UTC before comparison.
