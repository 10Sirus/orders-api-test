# Orders API - Repository Pattern Implementation

A production-grade REST API demonstrating idempotent operations, optimistic locking, transactional outbox pattern, and keyset pagination.

## Tech Stack
*   **Language:** Python 3.12
*   **Framework:** FastAPI (Async)
*   **Database:** PostgreSQL 15
*   **ORM:** SQLAlchemy 2.0 (Async) + Alembic
*   **Testing:** Pytest + AsyncIO

## Architecture

### Repository Pattern with DI
To ensure separation of concerns and testability:
- **Repositories**: Direct data access (`OrderRepository`, `IdempotencyRepository`, `OutboxRepository`).
- **Services**: Business logic (`OrderService`).
- **Dependency Injection**: Services receive repositories via DI; repositories receive the DB session via DI.

### Project Structure
```
app/
├── api/
│   ├── dependencies/       # Header extraction (tenant, idempotency, If-Match)
│   └── routers/            # API endpoints
├── core/                   # Config, logging, error handling
├── db/                     # Database session & base models
├── models/                 # SQLAlchemy ORM entities
├── repositories/           # Data access layer
├── services/               # Business logic layer
├── schemas/                # Pydantic DTOs
└── utils/                  # Pagination & Idempotency helpers
```

## Quick Start (Docker)

### 1. Run the Application
Builds the API and Postgres containers, applies migrations automatically, and starts the server.

```bash
docker compose up -d api
```
*   **API URL:** `http://localhost:8000`
*   **Swagger Docs:** `http://localhost:8000/docs`
*   **Database Port:** `5433` (Host)

### 2. Run Integration Tests
Tests run in a **separate, isolated container**. This command starts a test runner that connects to Postgres, generates a random temporary database (e.g., `test_db_x9s2`), runs the tests, and deletes the database immediately.

```bash
docker compose run --rm tests
```

### 3. Cleanup
To stop containers and remove database volumes:
```bash
docker compose down -v
```

## cURL Demo Sequence

Follow this sequence to test the full lifecycle of an order.

**1. Create a Draft Order (Idempotent)**
```bash
curl -X POST http://localhost:8000/orders \
  -H "X-Tenant-Id: tenant-1" \
  -H "Idempotency-Key: key-123" \
  -d "{}"
```
*Response: Note the `id` (e.g., `550e8400...`) and `version` (1).*

**2. Confirm the Order (Optimistic Locking)**
Replace `<ORDER_ID>` with the ID from step 1.
```bash
curl -X PATCH http://localhost:8000/orders/<ORDER_ID>/confirm \
  -H "X-Tenant-Id: tenant-1" \
  -H "If-Match: 1" \
  -H "Content-Type: application/json" \
  -d '{"totalCents": 5000}'
```
*Response: Status becomes `confirmed`, `version` bumps to 2.*

**3. Close the Order (Transactional Outbox)**
```bash
curl -X POST http://localhost:8000/orders/<ORDER_ID>/close \
  -H "X-Tenant-Id: tenant-1"
```
*Response: Status becomes `closed`. An event is written to the `outbox` table internally.*

**4. List Orders (Keyset Pagination)**
```bash
curl -X GET "http://localhost:8000/orders?limit=5" \
  -H "X-Tenant-Id: tenant-1"
```

