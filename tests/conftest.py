"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from libs.config import reset_settings
from services.api.app import create_app


@pytest.fixture
def client():
    """Create a test client for the API."""
    reset_settings()
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset configuration after each test."""
    yield
    reset_settings()
