"""Unit tests for logging utilities."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from app.utilities import logging


class TestLoggingContext:
    """Tests for logging context management."""

    def test_add_context_creates_new_context(self) -> None:
        """add_context should create a new context if none exists."""
        logging.clear_context()

        logging.add_context(request_id="123")

        context = logging.get_current_context()
        assert context["request_id"] == "123"

    def test_add_context_updates_existing_context(self) -> None:
        """add_context should update existing context with new values."""
        logging.clear_context()
        logging.add_context(request_id="123")

        logging.add_context(user_id="456")

        context = logging.get_current_context()
        assert context["request_id"] == "123"
        assert context["user_id"] == "456"

    def test_add_context_overwrites_existing_keys(self) -> None:
        """add_context should overwrite existing keys with new values."""
        logging.clear_context()
        logging.add_context(request_id="123")

        logging.add_context(request_id="789")

        context = logging.get_current_context()
        assert context["request_id"] == "789"

    def test_clear_context_removes_all_values(self) -> None:
        """clear_context should remove all context values."""
        logging.add_context(request_id="123", user_id="456")

        logging.clear_context()

        context = logging.get_current_context()
        assert "request_id" not in context
        assert "user_id" not in context

    def test_get_current_context_returns_empty_dict_when_cleared(self) -> None:
        """get_current_context should return empty dict after clear."""
        logging.clear_context()

        context = logging.get_current_context()

        assert context == {}

    def test_get_current_context_creates_context_if_none_exists(self) -> None:
        """get_current_context should create empty context if none exists."""
        logging.clear_context()
        logging._LOG_CONTEXT.set(None)

        context = logging.get_current_context()

        assert isinstance(context, dict)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger_with_correct_name(self) -> None:
        """get_logger should return a logger for the given name."""
        logger = logging.get_logger("test.module")

        # Verify it's our wrapper type
        assert isinstance(logger, logging._ContextLoggingWrapper)
        assert logger._logger.name == "test.module"


class TestContextLoggingWrapper:
    """Tests for the _ContextLoggingWrapper class."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self) -> Generator[None, Any, None]:
        """Clear context before each test."""
        logging.clear_context()
        yield
        logging.clear_context()

    def test_get_extra_params_includes_context(self) -> None:
        """_get_extra_params should include the current logging context."""
        logging.add_context(request_id="test-123")
        wrapper = logging._ContextLoggingWrapper(logging.logging.getLogger("test"))

        params = wrapper._get_extra_params(None)

        assert params["request_id"] == "test-123"

    def test_get_extra_params_merges_extra_with_context(self) -> None:
        """_get_extra_params should merge extra params with context."""
        logging.add_context(request_id="test-123")
        wrapper = logging._ContextLoggingWrapper(logging.logging.getLogger("test"))

        params = wrapper._get_extra_params({"custom": "value"})

        assert params["request_id"] == "test-123"
        assert params["custom"] == "value"

    def test_extra_params_override_context(self) -> None:
        """Extra params should take precedence over context values."""
        logging.add_context(request_id="original")
        wrapper = logging._ContextLoggingWrapper(logging.logging.getLogger("test"))

        params = wrapper._get_extra_params({"request_id": "overridden"})

        assert params["request_id"] == "overridden"
