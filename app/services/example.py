from __future__ import annotations

from typing import override

from app.services._common import AbstractContext
from app.services._common import ServiceError
from app.utilities import logging


logger = logging.get_logger(__name__)


class ExampleError(ServiceError):
    @override
    def service(self) -> str:
        return "example"

    NOT_FOUND = "not_found"


async def fetch_example(
    ctx: AbstractContext,
    id: int,
) -> ExampleError.OnSuccess[None]: ...
