from __future__ import annotations

from typing import override

from fastapi import status

from app.services._common import AbstractContext
from app.services._common import ServiceError
from app.utilities import logging

logger = logging.get_logger(__name__)


class HealthError(ServiceError):
    SERVICE_UNHEALTHY = "service_unhealthy"

    @override
    def service(self) -> str:
        return "health"

    @override
    def status_code(self) -> int:
        match self:
            case HealthError.SERVICE_UNHEALTHY:
                return status.HTTP_503_SERVICE_UNAVAILABLE
            case _:
                return status.HTTP_500_INTERNAL_SERVER_ERROR


# TODO: More comprehensive health check?
async def check_health(
    ctx: AbstractContext,
) -> HealthError.OnSuccess[None]:
    return None
