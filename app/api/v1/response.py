from __future__ import annotations

from typing import Any

from fastapi import status
from fastapi.responses import Response
from pydantic import BaseModel

from app.services import ServiceError
from app.services import is_error
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
    if is_error(service_response):
        logger.debug(
            "API call was interrupted by a service error.",
            extra={
                "error": service_response.resolve_name(),
                "status_code": service_response.status_code(),
            },
        )

        raise ServiceInterruptionException(
            create(
                data=service_response.resolve_name(),
                status=service_response.status_code(),
            ),
        )

    return service_response
