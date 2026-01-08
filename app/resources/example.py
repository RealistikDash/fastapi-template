from __future__ import annotations

from pydantic import BaseModel

from app.adapters.mysql import MySQLPoolAdapter


class ExampleResource(BaseModel):
    id: int

    ...


class ExampleRepository:
    __slots__ = ("_mysql",)

    def __init__(self, mysql: MySQLPoolAdapter) -> None:
        self._mysql: MySQLPoolAdapter = mysql
