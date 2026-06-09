# PriceRadar

[![CI](https://github.com/FabMin94/priceradar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/FabMin94/priceradar/actions/workflows/ci.yml)

An Amazon price tracker that monitors product prices on a schedule and triggers
alerts when prices drop below your threshold. Built as a microservice that
integrates with [AuthKit](https://github.com/FabMin94/authkit) for authentication.

---

## Architecture

```
Client (JWT token from AuthKit)
  │
  ▼
┌─────────────────────────────────┐
│        PriceRadar API           │
│                                 │
│  POST /products    add product  │
│  GET  /products    list tracked │
│  GET  /products/id price history│
│  DELETE /products/id   stop     │
│  GET  /alerts      price drops  │
└──────────┬──────────────────────┘
           │                    │
           ▼                    ▼
    PostgreSQL             AuthKit API
    ├── products         (token validation)
    ├── price_history
    └── alerts
           ▲
           │
┌───────────────────────┐
│  Background Scheduler │
│  Every 6 hours:       │
│  scrape → store →     │
│  alert if threshold   │
└───────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy (async) |
| Scraping | httpx + BeautifulSoup4 |
| Scheduling | APScheduler |
| Auth | Delegated to AuthKit |
| Testing | pytest + pytest-asyncio + httpx |
| Linting | ruff |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions → GHCR |

---

## Getting Started

### Prerequisites

- Python 3.12+
- Docker + Docker Compose
- [uv](https://github.com/astral-sh/uv)
- A running [AuthKit](https://github.com/FabMin94/authkit) instance

### 1. Clone and install

```bash
git clone https://github.com/FabMin94/priceradar.git
cd priceradar
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — set `AUTHKIT_URL` to your AuthKit instance:

```
AUTHKIT_URL=http://localhost:8000
```

### 3. Start the database

```bash
docker compose up -d db
```

### 4. Run the app

```bash
uv run python main.py
```

Visit `http://localhost:8001/docs` for the full API documentation.

---

## API Reference

All endpoints require a valid JWT token from AuthKit in the
`Authorization: Bearer <token>` header.

### Add a product

```http
POST /api/v1/products
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "url": "https://www.amazon.com/dp/B0CHXMJRP3",
  "name": "My Product",
  "alert_threshold": 99.99
}
```

Response `201`:
```json
{
  "id": "a1b2c3d4-...",
  "name": "My Product",
  "asin": "B0CHXMJRP3",
  "url": "https://www.amazon.com/dp/B0CHXMJRP3",
  "alert_threshold": "99.99",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z",
  "latest_price": null
}
```

### List tracked products

```http
GET /api/v1/products
Authorization: Bearer eyJhbGc...
```

### Get product with price history

```http
GET /api/v1/products/{id}
Authorization: Bearer eyJhbGc...
```

### Trigger manual scrape

```http
POST /api/v1/products/scrape
Authorization: Bearer eyJhbGc...
```

### List alerts

```http
GET /api/v1/alerts
Authorization: Bearer eyJhbGc...

# Unread only
GET /api/v1/alerts?unread_only=true
```

### Mark alert as read

```http
PATCH /api/v1/alerts/{id}/read
Authorization: Bearer eyJhbGc...
```

---

## Running Tests

```bash
# Start the database
docker compose up -d db

# Create test database
docker exec priceradar-db-1 psql -U priceradar -d priceradar_db \
  -c "CREATE DATABASE priceradar_test_db;"

# Run all tests
uv run pytest -v
```

---

## Project Structure

```
priceradar/
├── app/
│   ├── api/v1/        # Route handlers
│   ├── core/          # Config, Amazon utilities, AuthKit client
│   ├── db/            # Database connection, session
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── scrapers/      # Amazon scraper
│   └── services/      # Business logic, scheduler
├── tests/
│   ├── unit/          # Parser and utility tests
│   └── integration/   # Full API flow tests
├── docker-compose.yml
├── Dockerfile
└── main.py
```
