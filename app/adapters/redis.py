from __future__ import annotations

import asyncio
from collections.abc import Callable
from collections.abc import Coroutine
from typing import Self

from redis.asyncio import Redis

from app.utilities import logging

type PubSubHandler = Callable[[str], Coroutine[None, None, None]]

logger = logging.get_logger(__name__)

_TASK_QUEUE_SIZE = 100


class RedisClient(Redis):
    """A thin wrapper around the asynchronous Redis client, implementing PubSub functionality."""

    def __init__(
        self,
        host: str,
        port: int,
        database: int = 0,
        password: str | None = None,
    ) -> None:
        super().__init__(
            host=host,
            port=port,
            db=database,
            password=password,
            decode_responses=True,
        )

        self._pubsub_router = RedisPubsubRouter()
        self._tasks: asyncio.Queue[asyncio.Task[None]] = asyncio.Queue(_TASK_QUEUE_SIZE)
        self._pubsub_listen_lock = asyncio.Lock()
        self._pubsub_task: asyncio.Task[None] | None = None

    async def initialise(self) -> Self:
        """Initialises the Redis client, creating the PubSub task if necessary."""

        # Test connection by pinging Redis (ensure connection is established)
        await self.execute_command("PING")  # Sus

        if not self._pubsub_router.empty:
            await self.__create_pubsub_task()

        return self

    def register(
        self,
        channel: str,
    ) -> Callable[[PubSubHandler], PubSubHandler]:
        """Decorator for registering a new pubsub handler.

        Note: MUST be called before the Redis client is initialised.
        """

        if self.is_initialised:
            raise RuntimeError("Pubsub task already created!")
        return self._pubsub_router.register(channel)

    def include_router(self, router: RedisPubsubRouter) -> None:
        """Extends the main PubSub router with the routes of the given router."""

        if self.is_initialised:
            raise RuntimeError("Pubsub task already created!")
        self._pubsub_router.merge(router)

    async def __listen_pubsub(
        self,
    ) -> None:
        async with (
            self._pubsub_listen_lock,
            self.pubsub() as pubsub,
        ):
            for channel in self._pubsub_router.route_map():
                await pubsub.subscribe(channel)

            logger.info(
                "PubSub listener started.",
                extra={"channels": list(self._pubsub_router.route_map().keys())},
            )

            while True:
                message = await pubsub.get_message()
                if message is None:
                    continue

                if message.get("type") != "message":
                    continue

                handler = self._pubsub_router._get_handler(message["channel"])
                if handler is None:
                    logger.warning(
                        "No handler for subscribed channel!",
                        extra={
                            "channel": message["channel"],
                        },
                    )
                    continue

                # NOTE: Asyncio tasks can get GC'd, so we hold references in a queue.
                if self._tasks.full():
                    self._tasks.get_nowait()

                await self._tasks.put(
                    asyncio.create_task(
                        self.__safe_handle(
                            handler,
                            message["channel"],
                            message["data"],
                        ),
                    ),
                )

    async def __safe_handle(
        self,
        handler: PubSubHandler,
        channel: str,
        data: str,
    ) -> None:
        """Wraps handler execution with error handling to prevent individual
        handler failures from affecting other handlers or the listener."""
        try:
            await handler(data)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "PubSub handler raised an exception.",
                extra={"channel": channel},
            )

    async def __create_pubsub_task(self) -> asyncio.Task[None]:
        if self._pubsub_task is not None:
            raise RuntimeError("Pubsub listening task already created!")
        self._pubsub_task = asyncio.create_task(self.__listen_pubsub())
        return self._pubsub_task

    @property
    def is_initialised(self) -> bool:
        return self._pubsub_task is not None


class RedisPubsubRouter:
    """A router for Redis subscriptions."""

    __slots__ = (
        "_routes",
        "_prefix",
    )

    def __init__(
        self,
        *,
        prefix: str = "",
    ) -> None:
        self._routes: dict[str, PubSubHandler] = {}
        self._prefix = prefix

    @property
    def empty(self) -> bool:
        return not self._routes

    def register(
        self,
        channel: str,
    ) -> Callable[[PubSubHandler], PubSubHandler]:
        """Decorator for registering a new pubsub handler."""

        def decorator(handler: PubSubHandler) -> PubSubHandler:
            channel_name = self._prefix + channel
            self._routes[channel_name] = handler
            return handler

        return decorator

    def merge(self, other: Self) -> None:
        """Merges the routes of the given router into the current router."""

        for channel, handler in other.route_map().items():
            if channel in self._routes:
                logger.warning(
                    "Overwritten route when merging Redis routers!",
                    extra={
                        "channel": channel,
                    },
                )
            self._routes[channel] = handler

    def route_map(self) -> dict[str, PubSubHandler]:
        return self._routes

    def _get_handler(self, channel: str) -> PubSubHandler | None:
        return self._routes.get(channel)


def default() -> RedisClient:
    """Creates a default configuration for the Redis adapter using the `settings` module.
    It is provided as a convenience function to avoid repeating the initialisation code.

    Note:
        The connection still has to be initialised by calling `initialise()` on the returned instance.
    """

    from app import settings

    return RedisClient(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DATABASE,
    )
