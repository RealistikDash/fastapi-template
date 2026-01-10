from __future__ import annotations

import logging

from pydantic import BaseModel

from app.adapters.mysql import ImplementsMySQL

logger = logging.getLogger(__name__)


class ExampleResource(BaseModel):
    id: int

    ...


class ExampleRepository:
    __slots__ = ("_mysql",)

    def __init__(self, mysql: ImplementsMySQL) -> None:
        self._mysql = mysql
