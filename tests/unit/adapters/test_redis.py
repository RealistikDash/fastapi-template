"""Unit tests for Redis adapter and pubsub router."""

from __future__ import annotations

import pytest

from app.adapters import redis


class TestRedisPubsubRouter:
    """Tests for RedisPubsubRouter class."""

    def test_empty_returns_true_when_no_routes(self) -> None:
        """Router should report empty when no handlers are registered."""
        router = redis.RedisPubsubRouter()

        assert router.empty is True

    def test_empty_returns_false_after_registration(self) -> None:
        """Router should report non-empty after handler registration."""
        router = redis.RedisPubsubRouter()

        @router.register("test_channel")
        async def handler(data: str) -> None:
            pass

        assert router.empty is False

    def test_register_adds_handler_to_routes(self) -> None:
        """register decorator should add handler to route map."""
        router = redis.RedisPubsubRouter()

        @router.register("test_channel")
        async def handler(data: str) -> None:
            pass

        route_map = router.route_map()
        assert "test_channel" in route_map
        assert route_map["test_channel"] is handler

    def test_register_with_prefix(self) -> None:
        """Router prefix should be prepended to channel names."""
        router = redis.RedisPubsubRouter(prefix="app:")

        @router.register("events")
        async def handler(data: str) -> None:
            pass

        route_map = router.route_map()
        assert "app:events" in route_map
        assert "events" not in route_map

    def test_get_handler_returns_registered_handler(self) -> None:
        """_get_handler should return the correct handler for a channel."""
        router = redis.RedisPubsubRouter()

        @router.register("test_channel")
        async def handler(data: str) -> None:
            pass

        result = router._get_handler("test_channel")
        assert result is handler

    def test_get_handler_returns_none_for_unknown_channel(self) -> None:
        """_get_handler should return None for unregistered channels."""
        router = redis.RedisPubsubRouter()

        result = router._get_handler("unknown_channel")

        assert result is None

    def test_merge_combines_routes(self) -> None:
        """merge should combine routes from two routers."""
        router1 = redis.RedisPubsubRouter()
        router2 = redis.RedisPubsubRouter()

        @router1.register("channel1")
        async def handler1(data: str) -> None:
            pass

        @router2.register("channel2")
        async def handler2(data: str) -> None:
            pass

        router1.merge(router2)

        route_map = router1.route_map()
        assert "channel1" in route_map
        assert "channel2" in route_map

    def test_merge_overwrites_duplicate_channels(self) -> None:
        """merge should overwrite handlers for duplicate channel names."""
        router1 = redis.RedisPubsubRouter()
        router2 = redis.RedisPubsubRouter()

        @router1.register("shared_channel")
        async def handler1(data: str) -> None:
            pass

        @router2.register("shared_channel")
        async def handler2(data: str) -> None:
            pass

        router1.merge(router2)

        route_map = router1.route_map()
        assert route_map["shared_channel"] is handler2


class TestRedisClientRegistration:
    """Tests for RedisClient handler registration."""

    def test_is_initialised_returns_false_before_init(self) -> None:
        """is_initialised should be False before initialise() is called."""
        client = redis.RedisClient(
            host="localhost",
            port=6379,
            database=0,
        )

        assert client.is_initialised is False

    def test_register_returns_decorator(self) -> None:
        """register should return a decorator that registers the handler."""
        client = redis.RedisClient(
            host="localhost",
            port=6379,
            database=0,
        )

        @client.register("test_channel")
        async def handler(data: str) -> None:
            pass

        route_map = client._pubsub_router.route_map()
        assert "test_channel" in route_map

    def test_include_router_merges_routes(self) -> None:
        """include_router should merge external router's routes."""
        client = redis.RedisClient(
            host="localhost",
            port=6379,
            database=0,
        )
        router = redis.RedisPubsubRouter()

        @router.register("external_channel")
        async def handler(data: str) -> None:
            pass

        client.include_router(router)

        route_map = client._pubsub_router.route_map()
        assert "external_channel" in route_map

    def test_register_raises_after_initialised(self) -> None:
        """register should raise if called after client is initialised."""
        client = redis.RedisClient(
            host="localhost",
            port=6379,
            database=0,
        )
        # Simulate initialised state
        client._pubsub_task = object()  # type: ignore[assignment]

        with pytest.raises(RuntimeError, match="already created"):
            client.register("test_channel")

    def test_include_router_raises_after_initialised(self) -> None:
        """include_router should raise if called after client is initialised."""
        client = redis.RedisClient(
            host="localhost",
            port=6379,
            database=0,
        )
        router = redis.RedisPubsubRouter()
        # Simulate initialised state
        client._pubsub_task = object()  # type: ignore[assignment]

        with pytest.raises(RuntimeError, match="already created"):
            client.include_router(router)
