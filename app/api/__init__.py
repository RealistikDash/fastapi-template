from __future__ import annotations

import logging
import uuid
from typing import Awaitable
from typing import Callable

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from starlette.responses import Response

from app.adapters import mysql
from app.adapters import redis


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI()

    initialise_mysql(app)
    initialise_redis(app)
    initialise_request_tracing(app)

    create_routes(app)

    logger.debug("Finalised app instance.")
    return app


def create_routes(app: FastAPI) -> None:
    router = APIRouter(
        prefix="/api",
    )

    app.include_router(router)
    logger.debug("Attached routers to the app instance.")


def initialise_mysql(app: FastAPI) -> None:
    database = mysql.default()

    app.state.mysql = database

    # Lifecycle management
    @app.on_event("startup")
    async def on_startup() -> None:
        await app.state.mysql.connect()
        logger.info(
            "Connected to the MySQL database.",
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.mysql.disconnect()

    # Transaction management middleware
    @app.middleware("http")
    async def mysql_transaction(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ):  # TODO: Track request state with a UUID.
        # logger.debug(
        #    "Opened a new MySQL transaction for request.",
        #    extra={
        #        "uuid": request.state.uuid,
        #    },
        # )
        async with app.state.mysql.transaction() as sql:
            request.state.mysql = sql
            return await call_next(request)

    logger.debug(
        "Attached MySQL to the app instance.",
    )


def initialise_redis(app: FastAPI) -> None:
    app.state.redis = redis.default()

    # Lifecycle management
    @app.on_event("startup")
    async def on_startup() -> None:
        await app.state.redis.initialise()
        logger.info(
            "Connected to the Redis database.",
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.redis.aclose()
        logger.info(
            "Disconnected from the Redis database.",
        )

    logger.debug(
        "Attached Redis to the app instance.",
    )


def initialise_request_tracing(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_tracing(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.uuid = str(uuid.uuid4())
        return await call_next(request)
