"""
Pytest configuration for CENTINELA test suite.

Provides fixtures for:
- pytest-docker-compose: Docker Compose integration tests
- mockernetes: Kubernetes unit test mocking
- pytest-asyncio: Async test support
"""

import pytest

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio to use asyncio backend."""
    return "asyncio"


# Configure asyncio mode for pytest-asyncio
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.option.asyncio_mode = "auto"
