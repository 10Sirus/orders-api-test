# Orders API - Repository Pattern Implementation

Production-grade REST API with repository pattern, dependency injection, idempotent operations, optimistic locking, transactional outbox, and keyset pagination.

## Architecture

### Repository Pattern with DI

- **Repositories**: Data access layer (OrderRepository, IdempotencyRepository, OutboxRepository)
- **Services**: Business logic layer (OrderService)
- **Dependency Injection**: Services receive repositories via DI, repositories receive DB session via DI

### Project Structure

```
app/
├── api/
│   ├── dependencies/       # Header extraction (tenant, idempotency, If-Match)
│   └── routers/           # API endpoints
├── core/                  # Config, exceptions, error handlers, logging
├── db/                    # Session management, base
├── models/                # SQLAlchemy ORM models
├── repositories/          # Data access layer
├── services/              # Business logic layer
├── schemas/               # Pydantic DTOs
└── utils/                 # Pagination, idempotency utilities
```

## Quick Start (Docker)

### Prerequisites
- Docker: [Install Docker](https://docs.docker.com/get-docker/)  
- Docker Compose: included with Docker Desktop  
- Make sure Docker daemon is running

### 1. Run the Application
Builds the API and Postgres containers, applies migrations automatically, and starts the server.

```bash
docker compose up -d api
```
*   **API URL:** `http://localhost:8000`
*   **Swagger Docs:** `http://localhost:8000/docs`
*   **Database Port:** `5433` (Host)

### 2. Run the Integration Tests
Tests run in a **separate, isolated container**. 
*   This command starts a test runner that connects to Postgres.
*   It generates a random database (e.g., `test_db_x9s2`), runs the tests, and deletes the database immediately.
*   Your development data in `orders_db` is never touched.

```bash
docker compose run --rm tests
```

### 3. Stop and Cleanup
To stop the containers and remove the volumes (database data):

```bash
docker compose down -v
```

## API Endpoints

### POST /orders
Create draft order with idempotency.

**Headers**: `X-Tenant-Id`, `Idempotency-Key`

### PATCH /orders/{id}/confirm
Confirm order with optimistic locking.

**Headers**: `X-Tenant-Id`, `If-Match`  
**Body**: `{"totalCents": 1234}`

### POST /orders/{id}/close
Close order and create outbox entry (Transactional).

**Headers**: `X-Tenant-Id`

### GET /orders
List orders with keyset (cursor) pagination.

**Headers**: `X-Tenant-Id`  
**Query**: `limit`, `cursor`

