from sqlalchemy import text  # text() wraps a raw SQL string so SQLAlchemy knows it's intentional raw SQL, not a mistake.
from sqlalchemy.ext.asyncio import AsyncSession


async def ping(session: AsyncSession) -> None:  # async because database calls are I/O operations (they wait for a response)
    """Execute a minimal query to verify the database connection is alive."""
    await session.execute(text("SELECT 1"))  # await session.execute(...) — await means "pause here and wait for the database to respond, but let other requests run while we wait" — this is what makes the app async
