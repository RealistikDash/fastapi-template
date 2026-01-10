from __future__ import annotations

from pydantic import BaseModel

from app.adapters.mysql import ImplementsMySQL
from app.utilities import logging


logger = logging.get_logger(__name__)


class ExampleResource(BaseModel):
    id: int

    ...


class ExampleRepository:
    __slots__ = ("_mysql",)

    def __init__(self, mysql: ImplementsMySQL) -> None:
        self._mysql = mysql
