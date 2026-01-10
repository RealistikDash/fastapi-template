from __future__ import annotations

from typing import override

from app.services import AbstractContext
from app.services import ServiceError
from app.utilities import logging


logger = logging.get_logger(__name__)


class HealthError(ServiceError):
    @override
    def service(self) -> str:
        return "health"

    SERVICE_UNHEALTHY = "service_unhealthy"


# TODO: More comprehensive health check?
async def check_health(
    ctx: AbstractContext,
) -> HealthError.OnSuccess[None]:
    return None
