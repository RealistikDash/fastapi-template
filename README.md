# FastAPI Template

A production-ready FastAPI template with clean architecture, database adapters, and Docker support.

## Quick Start

```bash
# 1. Copy all example environment files
for f in configuration/*.example; do cp "$f" "${f%.example}"; done

# 2. Edit the copied files with your configuration
#    - configuration/app.env     → CORS settings, etc.
#    - configuration/mysql.env   → Database credentials

# 3. Create .env in project root for Docker Compose
cat > .env << 'EOF'
APP_EXTERNAL_PORT=8000
MYSQL_DATA_PATH=./mysql_data
PHPMYADMIN_EXTERNAL_PORT=8080
EOF

# 4. Build and run
make build
make run
```

The API is now available at `http://localhost:8000/api/v1/health`.

---

## Project Structure

```
app/
├── adapters/       # Database connections (MySQL, Redis)
├── api/            # HTTP layer (routes, request/response)
│   └── v1/         # API version 1
├── resources/      # Repositories (data access)
├── services/       # Business logic
├── settings.py     # Environment configuration
└── utilities/      # Helpers (logging, etc.)
```

**Data flows one way:** `API → Services → Resources → Adapters`

---

## Adding a New Feature

### Step 1: Create a Repository

Repositories handle database queries. Create `app/resources/users.py`:

```python
from __future__ import annotations

from pydantic import BaseModel
from app.adapters.mysql import ImplementsMySQL


class User(BaseModel):
    id: int
    email: str


class UserRepository:
    __slots__ = ("_mysql",)

    def __init__(self, mysql: ImplementsMySQL) -> None:
        self._mysql = mysql

    async def find_by_id(self, user_id: int) -> User | None:
        row = await self._mysql.fetch_one(
            "SELECT id, email FROM users WHERE id = :id",
            {"id": user_id},
        )
        return User(**row) if row else None

    async def create(self, email: str) -> User:
        user_id = await self._mysql.execute(
            "INSERT INTO users (email) VALUES (:email)",
            {"email": email},
        )
        return User(id=user_id, email=email)
```

### Step 2: Register in Context

Add to `app/services/_common.py`:

```python
from app.resources.users import UserRepository


class AbstractContext(ABC):
    # ... existing code ...

    @property
    def users(self) -> UserRepository:
        return UserRepository(self._mysql)
```

### Step 3: Create a Service

Services contain business logic. Create `app/services/users.py`:

```python
from __future__ import annotations

from typing import override
from fastapi import status

from app.services._common import AbstractContext
from app.services._common import ServiceError
from app.resources.users import User


class UserError(ServiceError):
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"

    @override
    def service(self) -> str:
        return "users"

    @override
    def status_code(self) -> int:
        match self:
            case UserError.NOT_FOUND:
                return status.HTTP_404_NOT_FOUND
            case UserError.ALREADY_EXISTS:
                return status.HTTP_409_CONFLICT
            case _:
                return status.HTTP_500_INTERNAL_SERVER_ERROR


async def get_user(
    ctx: AbstractContext,
    user_id: int,
) -> UserError.OnSuccess[User]:
    user = await ctx.users.find_by_id(user_id)
    if user is None:
        return UserError.NOT_FOUND
    return user
```

### Step 4: Create API Endpoints

Create `app/api/v1/users.py`:

```python
from __future__ import annotations

from fastapi import APIRouter
from fastapi import Response

from app.api.v1 import response
from app.api.v1.context import RequiresContext
from app.api.v1.context import RequiresTransaction
from app.services import users

router = APIRouter(prefix="/users")


# GET uses RequiresContext (read-only, uses connection pool)
@router.get("/{user_id}")
async def get_user(user_id: int, ctx: RequiresContext) -> Response:
    result = await users.get_user(ctx, user_id)
    return response.create(response.unwrap(result))


# POST uses RequiresTransaction (writes, uses database transaction)
@router.post("/")
async def create_user(email: str, ctx: RequiresTransaction) -> Response:
    result = await users.create_user(ctx, email)
    return response.create(response.unwrap(result))
```

### Step 5: Register the Router

In `app/api/v1/__init__.py`:

```python
from . import users


def create_router() -> APIRouter:
    router = APIRouter(prefix="/v1")
    router.include_router(health.router)
    router.include_router(users.router)  # Add this
    return router
```

---

## Key Concepts

### Context & Dependency Injection

Every endpoint receives a **context** that provides access to databases and repositories:

| Dependency | Use Case | What It Does |
|------------|----------|--------------|
| `RequiresContext` | Read operations (GET) | Uses connection pool directly |
| `RequiresTransaction` | Write operations (POST, PUT, DELETE) | Wraps in database transaction |

```python
# Reading data - no transaction needed
@router.get("/items")
async def list_items(ctx: RequiresContext) -> Response: ...


# Writing data - transaction auto-commits on success, rolls back on error
@router.post("/items")
async def create_item(ctx: RequiresTransaction) -> Response: ...
```

### Service Error Handling

Services return either a **success value** or an **error**. The `unwrap()` function handles this:

```python
async def get_user(ctx, user_id) -> UserError.OnSuccess[User]:
    user = await ctx.users.find_by_id(user_id)
    if user is None:
        return UserError.NOT_FOUND  # Returns error
    return user  # Returns success


# In API endpoint:
result = await users.get_user(ctx, user_id)
data = response.unwrap(result)  # Raises exception if error, returns User if success
```

This pattern avoids exceptions for expected errors (like "not found") while keeping code clean.

### Request Tracing

Every request gets a unique UUID. All logs during that request include this UUID:

```json
{"uuid": "abc-123", "message": "User created", "user_id": 42}
```

This makes debugging production issues much easier—search logs by UUID to see everything that happened in one request.

---

## Configuration

Environment files live in `configuration/`. Each `.example` file documents available options—copy them and fill in your values.

The root `.env` file configures Docker Compose (ports, volume paths). See the Quick Start for the required variables.

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make build` | Build Docker images |
| `make run` | Run app (foreground, see logs) |
| `make run-d` | Run app (background) |
| `make lint` | Run code quality checks |
| `make phpmyadmin` | Start PHPMyAdmin (development only) |

---

## Database Migrations

Migrations run automatically on startup. To create a new migration:

```bash
# Generate timestamp
TIMESTAMP=$(date +%s)

# Create migration files
touch migrations/migrations/${TIMESTAMP}_create_users.up.sql
touch migrations/migrations/${TIMESTAMP}_create_users.down.sql
```

**Example migration:**

```sql
-- migrations/migrations/1234567890_create_users.up.sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- migrations/migrations/1234567890_create_users.down.sql
DROP TABLE IF EXISTS users;
```

---

## Redis PubSub

Register handlers for Redis channels:

```python
# In your service or separate file
from app.adapters.redis import RedisPubsubRouter

pubsub_router = RedisPubsubRouter(prefix="myapp:")


@pubsub_router.register("user_created")
async def handle_user_created(data: str) -> None:
    # Handle the message
    print(f"User created: {data}")


# In app initialization, include the router:
# redis_client.include_router(pubsub_router)
```

---

## Logging

Logs are JSON-formatted for easy parsing. Use structured logging:

```python
from app.utilities import logging

logger = logging.get_logger(__name__)

# Good - structured data
logger.info("User created", extra={"user_id": 42, "email": "test@example.com"})

# Avoid - string interpolation
logger.info(f"User {user_id} created")  # Harder to search/filter
```

---

## Known Gotchas

### `from __future__ import annotations`

**Do NOT add this import to `app/api/v1/context.py`.**

It breaks FastAPI's dependency injection. All other files use it—this is the one exception. See the comment in that file for details.

### Middleware Order

Middleware runs in **reverse order** of registration. Request tracing is registered last so it runs first (wrapping everything else).

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Explicit transactions via DI | Avoids unnecessary transactions for read operations |
| Service errors as return values | Cleaner than exceptions for expected errors |
| Repository per resource | Single responsibility, easy to test |
| Context pattern | Dependency injection without global state |
| JSON logging | Machine-parseable, works with log aggregators |
| uvloop | ~2-4x faster than default asyncio event loop |

---

## Development Tips

1. **Start with the service layer** - Define your business logic before touching the API
2. **Use type hints everywhere** - The codebase is fully typed, keep it that way
3. **One service function = one operation** - Keep services focused
4. **Repositories are dumb** - They just fetch/store data, no business logic
5. **Test services, not endpoints** - Services are easier to test in isolation
