"""Unit tests for service common utilities and error handling."""

from __future__ import annotations

from typing import override

from fastapi import status

from app.services._common import ServiceError
from app.services._common import is_error
from app.services._common import is_success


class ExampleError(ServiceError):
    """Example error enum for testing purposes."""

    EXAMPLE_ERROR = "example_error"
    ANOTHER_ERROR = "another_error"

    @override
    def service(self) -> str:
        return "example"

    @override
    def status_code(self) -> int:
        match self:
            case ExampleError.EXAMPLE_ERROR:
                return status.HTTP_400_BAD_REQUEST
            case ExampleError.ANOTHER_ERROR:
                return status.HTTP_404_NOT_FOUND
            case _:
                return status.HTTP_500_INTERNAL_SERVER_ERROR


class TestServiceError:
    """Tests for ServiceError base class behaviour."""

    def test_resolve_name_returns_prefixed_value(self) -> None:
        """Error names should be prefixed with the service name."""
        error = ExampleError.EXAMPLE_ERROR

        result = error.resolve_name()

        assert result == "example.example_error"

    def test_status_code_returns_mapped_code(self) -> None:
        """Status codes should return the mapped HTTP status."""
        error = ExampleError.EXAMPLE_ERROR

        result = error.status_code()

        assert result == status.HTTP_400_BAD_REQUEST

    def test_different_errors_have_different_status_codes(self) -> None:
        """Different error variants can map to different status codes."""
        error_400 = ExampleError.EXAMPLE_ERROR
        error_404 = ExampleError.ANOTHER_ERROR

        assert error_400.status_code() == status.HTTP_400_BAD_REQUEST
        assert error_404.status_code() == status.HTTP_404_NOT_FOUND


class TestIsSuccess:
    """Tests for is_success type guard function."""

    def test_returns_true_for_non_error_value(self) -> None:
        """is_success should return True for successful values."""
        result: ExampleError.OnSuccess[str] = "success"

        assert is_success(result) is True

    def test_returns_true_for_none(self) -> None:
        """is_success should return True for None values (valid success)."""
        result: ExampleError.OnSuccess[None] = None

        assert is_success(result) is True

    def test_returns_false_for_error(self) -> None:
        """is_success should return False for ServiceError values."""
        result: ExampleError.OnSuccess[str] = ExampleError.EXAMPLE_ERROR

        assert is_success(result) is False


class TestIsError:
    """Tests for is_error type guard function."""

    def test_returns_true_for_error(self) -> None:
        """is_error should return True for ServiceError values."""
        result: ExampleError.OnSuccess[str] = ExampleError.EXAMPLE_ERROR

        assert is_error(result) is True

    def test_returns_false_for_success_value(self) -> None:
        """is_error should return False for successful values."""
        result: ExampleError.OnSuccess[str] = "success"

        assert is_error(result) is False

    def test_returns_false_for_none(self) -> None:
        """is_error should return False for None values."""
        result: ExampleError.OnSuccess[None] = None

        assert is_error(result) is False
