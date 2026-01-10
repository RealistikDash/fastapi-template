from __future__ import annotations

from typing import Any

from fastapi import status
from fastapi.responses import Response
from pydantic import BaseModel

from app.services._common import ServiceError
from app.services._common import is_success
from app.utilities import logging

logger = logging.get_logger(__name__)


class BaseResponse[T](BaseModel):
    """The base response model for all API v1 responses, in generic form."""

    status: int
    data: T


class ServiceInterruptionException(Exception):
    def __init__(self, response: Response) -> None:
        self.response = response


def create(data: Any, *, status: int = status.HTTP_200_OK) -> Response:
    """Creates a response from the base response model and the given data,
    following the API v1 response format."""

    model_json = BaseResponse(status=status, data=data).model_dump_json()
    return Response(
        content=model_json,
        media_type="application/json",
        status_code=status,
    )


def unwrap[T](service_response: ServiceError.OnSuccess[T]) -> T:
    if is_success(service_response):
        return service_response

    logger.debug(
        "API call was interrupted by a service error.",
        extra={
            "error": service_response,
        },
    )

    raise ServiceInterruptionException(
        create(
            data=service_response,
            # TODO: Determine appropriate status code.
            # For now, we assume a service interruption.
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        ),
    )
