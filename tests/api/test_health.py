"""API integration tests for the health endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for the /api/v1/health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health endpoint should return 200 status code."""
        response = await test_client.get("/api/v1/health/")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_response_format(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health endpoint should return properly formatted response."""
        response = await test_client.get("/api/v1/health/")

        data = response.json()
        assert "status" in data
        assert "data" in data
        assert data["status"] == 200

    @pytest.mark.asyncio
    async def test_health_check_data_is_null(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health endpoint should return null data on success."""
        response = await test_client.get("/api/v1/health/")

        data = response.json()
        assert data["data"] is None

    @pytest.mark.asyncio
    async def test_health_check_content_type(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health endpoint should return JSON content type."""
        response = await test_client.get("/api/v1/health/")

        assert response.headers["content-type"] == "application/json"
