from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,          # AsyncSession — represents one unit of work with the database. One HTTP request → one session. It tracks what you've changed and hasn't committed yet
    async_sessionmaker,    # a factory that creates AsyncSession objects on demand
    create_async_engine,   # create_async_engine — creates the connection pool to PostgreSQL. A "connection pool" is a set of pre-opened connections that get reused across requests, so you don't pay the cost of opening a new connection every time
)
from sqlalchemy.orm import DeclarativeBase

from saroweb.settings import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def _create_engine():
    settings = get_settings()
    return create_async_engine(
        settings.db_conn,         # the connection string from .env
        echo=settings.debug,      # if debug is true, print every SQL query to the terminal
        pool_pre_ping=True,       # before using a connection from the pool, send a quick "are you still alive?" check. Without this, if the database restarts, the pool might hand out a dead connection and your request crashes
    )


engine = _create_engine() # Runs once at startup. Creates the connection pool.

AsyncSessionLocal = async_sessionmaker(     # AsyncSessionLocal — a factory (a callable that creates sessions). The name Local is a SQLAlchemy convention meaning "thread/task-local session"
    engine,
    # by default SQLAlchemy marks all loaded objects as "expired" after a commit,
    # forcing a reload from DB on next access. 
    # We turn this off because in async code that reload can cause subtle bugs — we return the data before the session closes
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one DB session per request."""
    async with AsyncSessionLocal() as session: # async with AsyncSessionLocal() as session — opens a new session. The async with block guarantees the session is closed and cleaned up when the block exits, even if an error occurs
        yield session # this is a generator. It pauses here, hands the session to whoever called it, and waits. When the request is finished, execution returns here and the async with block closes the session

# Why yield instead of return? return session would close the function. 
# yield session means "pause here, let the request handler use the session, then come back and clean up." 
# FastAPI understands this pattern — when it sees Depends(get_session), it calls get_session, gets the yielded session, injects it into the endpoint, and after the endpoint finishes, resumes get_session to let it clean up.

