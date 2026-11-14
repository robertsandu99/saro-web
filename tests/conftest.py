import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import saroweb.models  # noqa: F401 — registers Squad, Player, Team with Base.metadata
from saroweb.app import create_app
from saroweb.database import Base, get_session
from saroweb.settings import get_settings


@pytest.fixture(scope="session")
def db_url() -> str:
    """Read the DB connection from settings and enforce the 'test' guard.

    Run tests like this (Git Bash):
      SARO_DB_CONN=postgresql+asyncpg://saroweb:saroweb@localhost:5434/saroweb_test \\
      SARO_SECRET_KEY=test-key-32-chars-long-padding-xx \\
      poetry run pytest -v

    The db-test service in docker-compose.yml listens on localhost:5434.
    """
    settings = get_settings()
    assert "test" in settings.db_conn.lower(), (
        "Tests must use a test database. "
        "Set SARO_DB_CONN to a connection string containing 'test'. "
        "Example: postgresql+asyncpg://saroweb:saroweb@localhost:5434/saroweb_test"
    )
    return settings.db_conn


@pytest_asyncio.fixture(scope="function")
async def test_engine(db_url: str):
    """Create all tables before each test, drop them after.

    scope="function" means every single test gets a completely empty database.
    This guarantees tests do not interfere with each other.
    """
    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        # create_all reads Base.metadata (populated by the import above) and
        # generates CREATE TABLE statements for every model
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        # drop_all removes every table — the next test starts completely fresh
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_engine):
    """HTTP client wired to the FastAPI app with the test DB injected.

    dependency_overrides replaces the real get_session with one that
    points to the isolated per-test database instead of the dev database.
    """
    Session = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_session():
        # same pattern as the real get_session — yield once, then clean up
        async with Session() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    # remove the override after the test so there is no cross-test pollution
    app.dependency_overrides.clear()
