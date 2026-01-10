"""Unit tests for API response utilities."""

from __future__ import annotations

import json
from typing import override

import pytest
from fastapi import status

from app.api.v1 import response
from app.services._common import ServiceError


class _MockError(ServiceError):
    """Mock error enum for response tests."""

    MOCK_ERROR = "mock_error"

    @override
    def service(self) -> str:
        return "mock"

    @override
    def status_code(self) -> int:
        return status.HTTP_400_BAD_REQUEST


class TestCreate:
    """Tests for response.create function."""

    def test_creates_response_with_default_status(self) -> None:
        """create should use 200 status by default."""
        result = response.create({"message": "success"})

        assert result.status_code == status.HTTP_200_OK

    def test_creates_response_with_custom_status(self) -> None:
        """create should use provided status code."""
        result = response.create(
            {"message": "created"},
            status=status.HTTP_201_CREATED,
        )

        assert result.status_code == status.HTTP_201_CREATED

    def test_response_body_contains_status(self) -> None:
        """Response body should include status field."""
        result = response.create("data")

        body = json.loads(bytes(result.body))
        assert body["status"] == status.HTTP_200_OK

    def test_response_body_contains_data(self) -> None:
        """Response body should include data field."""
        result = response.create({"key": "value"})

        body = json.loads(bytes(result.body))
        assert body["data"] == {"key": "value"}

    def test_response_media_type_is_json(self) -> None:
        """Response media type should be application/json."""
        result = response.create("data")

        assert result.media_type == "application/json"

    def test_handles_none_data(self) -> None:
        """create should handle None as data value."""
        result = response.create(None)

        body = json.loads(bytes(result.body))
        assert body["data"] is None


class TestUnwrap:
    """Tests for response.unwrap function."""

    def test_returns_success_value(self) -> None:
        """unwrap should return the value for successful results."""
        success_result: _MockError.OnSuccess[str] = "success_value"

        result = response.unwrap(success_result)

        assert result == "success_value"

    def test_returns_none_value(self) -> None:
        """unwrap should return None for successful None results."""
        success_result: _MockError.OnSuccess[None] = None

        result = response.unwrap(success_result)

        assert result is None

    def test_raises_for_error(self) -> None:
        """unwrap should raise ServiceInterruptionException for errors."""
        error_result: _MockError.OnSuccess[str] = _MockError.MOCK_ERROR

        with pytest.raises(response.ServiceInterruptionException):
            response.unwrap(error_result)

    def test_exception_contains_error_response(self) -> None:
        """ServiceInterruptionException should contain formatted response."""
        error_result: _MockError.OnSuccess[str] = _MockError.MOCK_ERROR

        with pytest.raises(response.ServiceInterruptionException) as exc_info:
            response.unwrap(error_result)

        error_response = exc_info.value.response
        assert error_response.status_code == status.HTTP_400_BAD_REQUEST

        body = json.loads(bytes(error_response.body))
        assert body["data"] == "mock.mock_error"


class TestBaseResponse:
    """Tests for BaseResponse model."""

    def test_model_serialisation(self) -> None:
        """BaseResponse should serialise correctly to JSON."""
        model = response.BaseResponse(status=200, data={"key": "value"})

        result = model.model_dump_json()
        parsed = json.loads(result)

        assert parsed["status"] == 200
        assert parsed["data"] == {"key": "value"}

    def test_model_with_none_data(self) -> None:
        """BaseResponse should handle None data."""
        model = response.BaseResponse(status=200, data=None)

        result = model.model_dump_json()
        parsed = json.loads(result)

        assert parsed["data"] is None
