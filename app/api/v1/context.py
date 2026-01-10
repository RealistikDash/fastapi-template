# DO NOT UNCOMMENT THE FUTURE IMPORT. This breaks the entirety of
# FastAPI's dependency injection system (somehow?).
# from __future__ import annotations

from typing import Annotated
from typing import override

from fastapi import Request
from fastapi import Depends

from app.services._common import AbstractContext
from app.adapters.mysql import ImplementsMySQL
from app.adapters.redis import RedisClient


class HTTPContext(AbstractContext):
    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    @override
    def _mysql(self) -> ImplementsMySQL:
        return self.request.state.mysql

    @property
    @override
    def _redis(self) -> RedisClient:
        return self.request.app.state.redis


RequiresContext = Annotated[HTTPContext, Depends(HTTPContext)]
"""A type alias for dependencies that require the context to be injected."""
