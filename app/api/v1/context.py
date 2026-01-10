# =============================================================================
# WARNING: DO NOT ADD `from __future__ import annotations` TO THIS FILE
# =============================================================================
#
# FastAPI's dependency injection relies on runtime type introspection to resolve
# dependencies. When `from __future__ import annotations` is enabled (PEP 563),
# all annotations become forward references (strings) that are evaluated lazily.

# The workaround is to NOT use `from __future__ import annotations` in files
# that define FastAPI dependencies. All other files in this codebase use it.
# =============================================================================

from collections.abc import AsyncGenerator
from typing import Annotated
from typing import override

from fastapi import Depends
from fastapi import Request

from app.adapters.mysql import ImplementsMySQL
from app.adapters.mysql import MySQLPoolAdapter
from app.adapters.redis import RedisClient
from app.services import AbstractContext


class HTTPContext(AbstractContext):
    """Context for read-only operations using the connection pool directly."""

    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    @override
    def _mysql(self) -> ImplementsMySQL:
        return self.request.app.state.mysql

    @property
    @override
    def _redis(self) -> RedisClient:
        return self.request.app.state.redis


class HTTPTransactionContext(AbstractContext):
    """Context for write operations using an explicit transaction."""

    def __init__(self, mysql: ImplementsMySQL, redis: RedisClient) -> None:
        self._mysql_conn = mysql
        self._redis_conn = redis

    @property
    @override
    def _mysql(self) -> ImplementsMySQL:
        return self._mysql_conn

    @property
    @override
    def _redis(self) -> RedisClient:
        return self._redis_conn


async def _get_transaction_context(
    request: Request,
) -> AsyncGenerator[HTTPTransactionContext, None]:
    """Dependency that provides a context with an active database transaction."""
    pool: MySQLPoolAdapter = request.app.state.mysql
    redis_client: RedisClient = request.app.state.redis

    async with pool.transaction() as transaction:
        yield HTTPTransactionContext(transaction, redis_client)


RequiresContext = Annotated[HTTPContext, Depends(HTTPContext)]
"""A type alias for read-only operations using the connection pool."""

RequiresTransaction = Annotated[
    HTTPTransactionContext,
    Depends(_get_transaction_context),
]
"""A type alias for write operations that require an explicit database transaction."""
