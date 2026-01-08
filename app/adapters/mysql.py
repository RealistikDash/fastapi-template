from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncGenerator
from collections.abc import Mapping
from typing import Any
from typing import Protocol
from typing import override

from databases import Database
from databases import DatabaseURL
from databases.core import Connection
from databases.core import Transaction
from databases.interfaces import Record

type MySQLValue = Any
type MySQLRow = Mapping[str, MySQLValue]
type MySQLValues = dict[str, MySQLValue]

logger = logging.getLogger(__name__)


# Databases 0.5.0 broke mapping access, raising a silent DeprecationWarning.
# This kills CPU, so we workaround it by accessing a direct mapping.
def _mapping(record: Record | None) -> MySQLRow | None:
    if record is None:
        return None
    return record._mapping  # noqa: SLF001


def _mapping_list(records: list[Record]) -> list[MySQLRow]:
    return [record._mapping for record in records]  # noqa: SLF001


class _MySQLQueryableProtocol(Protocol):
    """A protocol defining a queryable MySQL source."""

    async def execute(self, query: str, values: MySQLValues | None = None) -> Any: ...
    async def fetch_one(
        self,
        query: str,
        values: MySQLValues | None = None,
    ) -> Record | None: ...
    async def fetch_all(
        self,
        query: str,
        values: MySQLValues | None = None,
    ) -> list[Record]: ...
    async def fetch_val(self, query: str, values: MySQLValues | None = None) -> Any: ...
    async def iterate(
        self,
        query: str,
        values: MySQLValues | None = None,
    ) -> AsyncGenerator[Mapping, None]: ...


class ImplementsMySQL(ABC):
    """An abstract class that implements MySQL query methods."""

    @property
    @abstractmethod
    def _connection(self) -> _MySQLQueryableProtocol: ...

    async def fetch_one(
        self,
        query: str,
        values: MySQLValues | None = None,
    ) -> MySQLRow | None:
        res = await self._connection.fetch_one(query, values)
        return _mapping(res)

    async def fetch_all(
        self,
        query: str,
        values: MySQLValues | None = None,
    ) -> list[MySQLRow]:
        res = await self._connection.fetch_all(query, values)
        return _mapping_list(res)

    async def fetch_val(
        self,
        query: str,
        values: MySQLValues | None = None,
    ) -> Any:
        res = await self._connection.fetch_val(query, values)
        return res

    async def execute(self, query: str, values: MySQLValues | None = None) -> Any:
        return await self._connection.execute(query, values)

    def iterate(
        self,
        query: str,
        values: MySQLValues | None = None,
    ) -> AsyncGenerator[MySQLRow, None]:
        return self._connection.iterate(query, values)  # type: ignore


class MySQLPoolAdapter(ImplementsMySQL):
    """A pool of MySQL connections that can be used to execute queries or
    transactions."""

    def __init__(self, database_url: DatabaseURL) -> None:
        self._pool = Database(database_url)

    @property
    @override
    def _connection(self) -> _MySQLQueryableProtocol:
        # The type ignore here is just because we don't account for SQLAlchemy
        # support in our protocol.
        return self._pool  # type: ignore

    async def connect(self) -> None:
        await self._pool.connect()

    async def disconnect(self) -> None:
        await self._pool.disconnect()

    def transaction(self) -> MySQLTransaction:
        return MySQLTransaction(self._pool)


class MySQLTransaction(ImplementsMySQL):
    """A wrapper around a transaction that implements the same interface as
    `MySQLService`."""

    # Slots are justified due to the frequency of initialisation.
    __slots__ = ("_backend_pool", "_current_connection", "_transaction")

    def __init__(self, backend_pool: Database) -> None:
        self._backend_pool: Database = backend_pool
        self._current_connection: Connection | None = None
        self._transaction: Transaction | None = None

    async def __aenter__(self) -> MySQLTransaction:
        self._current_connection = await self._backend_pool.connection().__aenter__()
        self._transaction = await self._current_connection.transaction().__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        # This handles rollback on exception using `args`.
        if self._transaction is not None:
            await self._transaction.__aexit__(*args)

        if self._current_connection is not None:
            await self._current_connection.__aexit__(*args)

    @property
    @override
    def _connection(self) -> _MySQLQueryableProtocol:
        # assert self._current_connection is not None
        return self._current_connection  # type: ignore


def default() -> ImplementsMySQL:
    """Creates a default configuration for the MySQL adapter using the `settings` module.
    It is provided as a convenience function to avoid repeating the initialisation code.

    Note:
        The connection still has to be initialised by calling `connect()` on the returned instance.
    """

    import urllib.parse

    from app import settings

    try:
        import asyncmy  # noqa: F401 # type: ignore[import]

        protocol = "mysql+asyncmy"
        logger.debug("Using asyncmy as the MySQL driver.")
    except ImportError:
        logger.debug("Using Databases' default MySQL driver.")
        protocol = "mysql"

    database_url = DatabaseURL(
        "{protocol}://{username}:{password}@{host}:{port}/{db}".format(
            protocol=protocol,
            username=settings.MYSQL_USER,
            password=urllib.parse.quote(settings.MYSQL_PASSWORD),
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_TCP_PORT,
            db=settings.MYSQL_DATABASE,
        ),
    )

    mysql = MySQLPoolAdapter(database_url)
    return mysql
