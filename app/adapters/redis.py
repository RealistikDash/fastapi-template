from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Coroutine
from queue import Queue
from typing import Self

from redis.asyncio import Redis

type PubSubHandler = Callable[[str], Coroutine[None, None, None]]

logger = logging.getLogger(__name__)


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

        self._default_initialise = self.initialize
        del self.initialize

        self._pubsub_router = RedisPubsubRouter()
        self._tasks: Queue[Awaitable[None]] = Queue(100)
        self._pubsub_listen_lock = asyncio.Lock()
        self._pubsub_task: asyncio.Task[None] | None = None

    async def initialise(self) -> Self:
        """Initialises the Redis client, creating the PubSub task if necessary."""

        if not self._pubsub_router.empty:
            await self.__create_pubsub_task()

        return await self._default_initialise()

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

                # NOTE: Asyncio tasks can get GC'd lmfao.
                if self._tasks.full():
                    self._tasks.get()

                self._tasks.put(asyncio.create_task(handler(message["data"])))

                # NOTE: Loop handoff to prevent blocking the event loop.
                await asyncio.sleep(0)

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
