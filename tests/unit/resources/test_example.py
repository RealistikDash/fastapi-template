"""Unit tests for the example resource and repository."""

from __future__ import annotations

from app.resources import example
from tests.conftest import MockMySQLAdapter


class TestExampleResource:
    """Tests for ExampleResource model."""

    def test_model_creation(self) -> None:
        """ExampleResource should be creatable with valid data."""
        resource = example.ExampleResource(id=1)

        assert resource.id == 1

    def test_model_serialisation(self) -> None:
        """ExampleResource should serialise to dict correctly."""
        resource = example.ExampleResource(id=42)

        data = resource.model_dump()

        assert data["id"] == 42


class TestExampleRepository:
    """Tests for ExampleRepository class."""

    def test_repository_initialises_with_mysql(self) -> None:
        """ExampleRepository should store MySQL adapter reference."""
        mock_mysql = MockMySQLAdapter()

        repository = example.ExampleRepository(mock_mysql)

        assert repository._mysql is mock_mysql
