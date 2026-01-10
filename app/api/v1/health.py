from __future__ import annotations

from fastapi import APIRouter
from fastapi import Response

from app.api.v1 import response
from app.api.v1.context import RequiresContext
from app.services import health

router = APIRouter(
    prefix="/health",
)

type HealthResponse = response.BaseResponse[None]


@router.get("/", response_model=HealthResponse)
async def health_check(
    ctx: RequiresContext,
) -> Response:
    status = await health.check_health(ctx)
    status = response.unwrap(status)

    return response.create(status)
