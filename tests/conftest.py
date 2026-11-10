import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from saroweb.app import app
from saroweb.settings import get_settings


@pytest.fixture(scope="session", autouse=True)
def enforce_test_env():
    """Fail fast if someone accidentally runs tests against a non-test DB."""
    settings = get_settings()
    assert "test" in settings.db_conn.lower(), (
        "Tests must run against a test database. "
        "Set SARO_DB_CONN to a connection string containing 'test'."
    )


@pytest_asyncio.fixture(scope="session")
async def client():
    """Async HTTP client wired directly to the FastAPI app (no real network)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
