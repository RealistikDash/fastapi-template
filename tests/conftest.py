"""Shared test fixtures and configuration for all tests."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any
from typing import override
from unittest import mock

import pytest
import pytest_asyncio
from httpx import ASGITransport
from httpx import AsyncClient


def _ensure_test_env() -> None:
    """Ensure minimal environment variables are set for testing."""
    defaults = {
        "APP_COMPONENT": "fastapi",
        "MYSQL_HOST": "localhost",
        "MYSQL_TCP_PORT": "3306",
        "MYSQL_USER": "test",
        "MYSQL_PASSWORD": "test",
        "MYSQL_DATABASE": "test",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_DATABASE": "0",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


_ensure_test_env()

from app.adapters import mysql
from app.adapters import redis
from app.adapters.redis import RedisClient
from app.services._common import AbstractContext


class _MockMySQLConnection:
    """Internal mock connection that implements the MySQL queryable protocol."""

    def __init__(self, results: dict[str, Any]) -> None:
        self._results = results

    async def fetch_one(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> Any:
        for pattern, result in self._results.items():
            if pattern in query:
                return result
        return None

    async def fetch_all(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> list[Any]:
        for pattern, result in self._results.items():
            if pattern in query:
                return result if isinstance(result, list) else [result]
        return []

    async def fetch_val(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> Any:
        for pattern, result in self._results.items():
            if pattern in query:
                return result
        return None

    async def execute(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> Any:
        return None

    async def iterate(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        results = await self.fetch_all(query, values)
        for result in results:
            yield result


class MockMySQLAdapter(mysql.ImplementsMySQL):
    """A mock MySQL adapter for testing purposes."""

    def __init__(self) -> None:
        self._results: dict[str, Any] = {}
        self._mock_connection = _MockMySQLConnection(self._results)

    @property
    def _connection(self) -> _MockMySQLConnection:  # type: ignore[override]
        return self._mock_connection

    def set_result(self, query_pattern: str, result: Any) -> None:
        """Set a mock result for queries containing the given pattern."""
        self._results[query_pattern] = result

    async def fetch_one(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Override to return dicts directly without _mapping."""
        return await self._mock_connection.fetch_one(query, values)

    async def fetch_all(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Override to return dicts directly without _mapping."""
        return await self._mock_connection.fetch_all(query, values)

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    def transaction(self) -> MockMySQLTransaction:
        return MockMySQLTransaction(self)


class MockMySQLTransaction:
    """A mock MySQL transaction for testing purposes."""

    def __init__(self, adapter: MockMySQLAdapter) -> None:
        self._adapter = adapter

    async def __aenter__(self) -> MockMySQLTransaction:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    async def fetch_one(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return await self._adapter.fetch_one(query, values)

    async def fetch_all(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self._adapter.fetch_all(query, values)

    async def fetch_val(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> Any:
        return await self._adapter.fetch_val(query, values)

    async def execute(
        self,
        query: str,
        values: dict[str, Any] | None = None,
    ) -> Any:
        return await self._adapter.execute(query, values)


class MockRedisClient:
    """A mock Redis client for testing purposes."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._pubsub_handlers: dict[str, Any] = {}

    async def initialise(self) -> MockRedisClient:
        return self

    async def get(self, key: str) -> Any:
        return self._data.get(key)

    async def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def aclose(self) -> None:
        pass

    def set_data(self, key: str, value: Any) -> None:
        """Helper to preset data for testing."""
        self._data[key] = value

    def clear_data(self) -> None:
        """Helper to clear all stored data."""
        self._data.clear()


class MockContext(AbstractContext):
    """A mock context for testing services without real database connections."""

    def __init__(
        self,
        mysql_adapter: MockMySQLAdapter | None = None,
        redis_client: MockRedisClient | None = None,
    ) -> None:
        self._mysql_adapter = mysql_adapter or MockMySQLAdapter()
        self._redis_client = redis_client or MockRedisClient()

    @property
    @override
    def _mysql(self) -> MockMySQLAdapter:  # type: ignore[override]
        return self._mysql_adapter

    @property
    @override
    def _redis(self) -> MockRedisClient:  # type: ignore[override]
        return self._redis_client


@pytest.fixture
def mock_mysql() -> MockMySQLAdapter:
    """Provides a mock MySQL adapter for unit tests."""
    return MockMySQLAdapter()


@pytest.fixture
def mock_redis() -> MockRedisClient:
    """Provides a mock Redis client for unit tests."""
    return MockRedisClient()


@pytest.fixture
def mock_context(
    mock_mysql: MockMySQLAdapter,
    mock_redis: MockRedisClient,
) -> MockContext:
    """Provides a mock context for service unit tests."""
    return MockContext(mock_mysql, mock_redis)


@pytest_asyncio.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an async HTTP client for API integration tests.

    This fixture patches the MySQL and Redis adapters with mocks to avoid
    requiring actual database connections during tests.
    """
    mock_mysql_adapter = MockMySQLAdapter()
    mock_redis_client = MockRedisClient()

    def mock_mysql_default() -> MockMySQLAdapter:
        return mock_mysql_adapter

    def mock_redis_default() -> MockRedisClient:
        return mock_redis_client

    with (
        mock.patch.object(mysql, "default", mock_mysql_default),
        mock.patch.object(redis, "default", mock_redis_default),
    ):
        # Import here to ensure patches are applied before app creation
        from app import api

        app = api.create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),  # type: ignore[arg-type]
            base_url="http://test",
        ) as client:
            yield client


@pytest.fixture
def anyio_backend() -> str:
    """Configure anyio to use asyncio."""
    return "asyncio"
