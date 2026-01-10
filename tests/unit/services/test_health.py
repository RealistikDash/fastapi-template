"""Unit tests for the health service."""

from __future__ import annotations

import pytest

from app.services import health
from app.services._common import is_success
from tests.conftest import MockContext


class TestCheckHealth:
    """Tests for the check_health service function."""

    @pytest.mark.asyncio
    async def test_returns_none_on_success(
        self,
        mock_context: MockContext,
    ) -> None:
        """Health check should return None when successful."""
        result = await health.check_health(mock_context)

        assert result is None
        assert is_success(result)


class TestHealthError:
    """Tests for HealthError enum."""

    def test_service_name_is_health(self) -> None:
        """HealthError should return 'health' as the service name."""
        error = health.HealthError.SERVICE_UNHEALTHY

        assert error.service() == "health"

    def test_resolve_name_format(self) -> None:
        """HealthError should resolve to 'health.<error_value>' format."""
        error = health.HealthError.SERVICE_UNHEALTHY

        assert error.resolve_name() == "health.service_unhealthy"

    def test_service_unhealthy_returns_503(self) -> None:
        """SERVICE_UNHEALTHY error should return 503 status code."""
        error = health.HealthError.SERVICE_UNHEALTHY

        assert error.status_code() == 503
