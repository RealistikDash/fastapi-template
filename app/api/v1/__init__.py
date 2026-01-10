from __future__ import annotations

from fastapi import APIRouter

from . import example


def create_router() -> APIRouter:
    router = APIRouter(
        prefix="/v1",
    )

    router.include_router(example.router)

    return router
