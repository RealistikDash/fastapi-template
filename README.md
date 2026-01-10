# FastAPI Template

A production-ready FastAPI template repository with a clean architecture, comprehensive database adapters, structured logging, and Docker support. This template follows best practices for maintainable, type-safe Python applications.

## Features

- **FastAPI** with async/await support
- **MySQL** adapter with transaction management middleware
- **Redis** adapter with PubSub support
- **Structured JSON logging** with request tracing
- **Docker & Docker Compose** setup for development
- **Type-safe** codebase with comprehensive type hints
- **Clean architecture** with clear separation of concerns
- **Service error handling** with typed error responses
- **Request context** injection for services

## Architecture

The codebase follows a layered architecture:

```
app/
├── adapters/          # Database adapters (MySQL, Redis)
├── api/              # FastAPI routes and HTTP layer
│   └── v1/           # API version 1
├── resources/        # Data access layer (repositories)
├── services/         # Business logic layer
├── settings.py       # Configuration management
└── utilities/        # Shared utilities (logging, event loop)
```

### Layer Responsibilities

- **Adapters** (`app/adapters/`): Database connection management and query interfaces
- **Resources** (`app/resources/`): Repository pattern for data access
- **Services** (`app/services/`): Business logic and domain operations
- **API** (`app/api/`): HTTP endpoints, request/response handling, and routing

### Key Patterns

- **Context Pattern**: Services receive an `AbstractContext` that provides access to database adapters
- **Error Handling**: Services return `ServiceError.OnSuccess[T]` for type-safe error handling
- **Transaction Management**: Automatic MySQL transaction per HTTP request via middleware
- **Request Tracing**: UUID-based request tracing for log correlation

## Setup

### Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)

### Initial Setup

1. **Clone and customize the repository name:**
   ```bash
   # Update Docker image names in docker-compose.yaml
   # Change "app:latest" to your service name
   ```

2. **Configure environment variables:**
   ```bash
   # Copy example files
   cp configuration/app.env.example configuration/app.env
   cp configuration/mysql.env.example configuration/mysql.env
   
   # Edit configuration/app.env and add:
   APP_COMPONENT=fastapi
   
   # Edit configuration/mysql.env and configure:
   MYSQL_ROOT_PASSWORD=your_root_password
   MYSQL_DATABASE=your_database_name
   MYSQL_USER=your_user
   MYSQL_PASSWORD=your_password
   ```

3. **Build and run:**
   ```bash
   make build
   make run
   ```

   Or using Docker Compose directly:
   ```bash
   docker compose build
   docker compose up app
   ```

The API will be available at `http://localhost:${APP_EXTERNAL_PORT}` (default port configured in `docker-compose.yaml`).

## Development

### Make Commands

- `make build` - Build Docker images
- `make run` - Run the application (foreground)
- `make run-d` - Run the application (detached/background)
- `make lint` - Run pre-commit hooks

### Project Structure

#### Adding a New Feature

1. **Create a Repository** (`app/resources/`):
   ```python
   # app/resources/my_feature.py
   from app.adapters.mysql import ImplementsMySQL
   
   class MyFeatureRepository:
       def __init__(self, mysql: ImplementsMySQL) -> None:
           self._mysql = mysql
   ```

2. **Register the Repository** in `app/services/_common.py`:
   ```python
   # Add to AbstractContext class
   @property
   def my_feature(self) -> MyFeatureRepository:
       return MyFeatureRepository(self._mysql)
   ```

3. **Create a Service** (`app/services/`):
   ```python
   # app/services/my_feature.py
   from app.services import AbstractContext, ServiceError
   
   class MyFeatureError(ServiceError):
       def service(self) -> str:
           return "my_feature"
       
       NOT_FOUND = "not_found"
   
   async def get_my_feature(
       ctx: AbstractContext,
       id: int,
   ) -> MyFeatureError.OnSuccess[MyFeatureModel]:
       # Business logic here
       ...
   ```

4. **Create API Endpoints** (`app/api/v1/`):
   ```python
   # app/api/v1/my_feature.py
   from fastapi import APIRouter
   from app.api.v1.context import RequiresContext
   from app.api.v1.response import create, unwrap
   from app.services import my_feature
   
   router = APIRouter(prefix="/my-feature")
   
   @router.get("/{id}")
   async def get_my_feature(
       id: int,
       ctx: RequiresContext,
   ):
       result = await my_feature.get_my_feature(ctx, id)
       return create(unwrap(result))
   ```

5. **Register the Router** in `app/api/v1/__init__.py`:
   ```python
   from . import my_feature
   
   def create_router() -> APIRouter:
       router = APIRouter(prefix="/v1")
       router.include_router(my_feature.router)
       return router
   ```

## Configuration

### Environment Variables

The application uses environment variables loaded from `.env` files via `python-dotenv`. Key variables:

- `APP_COMPONENT`: Component type (e.g., `fastapi`)
- `MYSQL_HOST`, `MYSQL_TCP_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`: MySQL connection settings
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DATABASE`: Redis connection settings

### Logging

Logging is configured via `logging.yaml` and uses structured JSON logging. Request tracing automatically adds a UUID to each request for log correlation.

## Database Adapters

### MySQL

- Connection pooling via `databases` library
- Automatic transaction management per HTTP request
- Transaction context available via `request.state.mysql`
- Supports both `asyncmy` and default MySQL drivers

### Redis

- Async Redis client with PubSub support
- PubSub handlers can be registered via decorators
- Automatic connection lifecycle management

## Migrations

This template uses [golang-migrate](https://github.com/golang-migrate/migrate) for database migrations. Migrations are automatically run before the application starts via a Docker service.

### Migration Structure

Migrations are stored in `migrations/migrations/` and follow the naming convention:
- `{timestamp}_{name}.up.sql` - Forward migration
- `{timestamp}_{name}.down.sql` - Rollback migration

Example:
```
migrations/
└── migrations/
    ├── 1768060473_example.up.sql
    └── 1768060473_example.down.sql
```

### Creating Migrations

1. **Generate a timestamp:**
   ```bash
   date +%s
   # Example output: 1768060473
   ```

2. **Create migration files:**
   ```bash
   # Create up migration
   touch migrations/migrations/$(date +%s)_create_users_table.up.sql
   
   # Create down migration
   touch migrations/migrations/$(date +%s)_create_users_table.down.sql
   ```

3. **Write your SQL:**
   ```sql
   -- migrations/migrations/1768060473_create_users_table.up.sql
   CREATE TABLE users (
       id INT AUTO_INCREMENT PRIMARY KEY,
       email VARCHAR(255) NOT NULL UNIQUE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

   ```sql
   -- migrations/migrations/1768060473_create_users_table.down.sql
   DROP TABLE IF EXISTS users;
   ```

### Running Migrations

Migrations run automatically when you start the application with Docker Compose. The migrations service:
- Waits for MySQL to be healthy
- Runs all pending migrations
- Completes before the app service starts

To manually run migrations (if needed):
```bash
docker compose run --rm migrations
```

### Development

- `pre-commit` - Git hooks for code quality

See `requirements/main.txt` and `requirements/dev.txt` for complete dependency lists.
