from __future__ import annotations

from fastapi import APIRouter


def create_router() -> APIRouter:
    router = APIRouter(
        prefix="/v1",
    )

    return router
