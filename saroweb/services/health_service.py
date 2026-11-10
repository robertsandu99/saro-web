from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.repositories import health_repository


async def check_database(session: AsyncSession) -> dict[str, str]:
    """Verify the application is running and the database is reachable."""
    await health_repository.ping(session) # It calls health_repository.ping(session) and passes the same session down — same transaction
    return {"status": "ok"}  # If ping succeeds, we return {"status": "ok"} — FastAPI will convert this dict to JSON automatically

