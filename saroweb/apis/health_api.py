from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.database import get_session
from saroweb.services import health_service

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
async def health_check(session: AsyncSession = Depends(get_session)):  # Depends — FastAPI's dependency injection system. Depends(get_session) means "before running this endpoint, call get_session() and pass the result as the session argument"
    """
    'session: AsyncSession = Depends(get_session)' — this is dependency injection.
    When a request hits /health, FastAPI calls get_session(), gets a session, and passes it here as session.
    The : AsyncSession is the type annotation so the editor knows what session is.
    The = Depends(get_session) is the default value — but instead of a plain value it's an instruction to FastAPI to call get_session() first
    return await health_service.check_database(session) — calls the service, awaits the async result, and returns it.
    FastAPI automatically converts {"status": "ok"} to a JSON HTTP response
    """
    return await health_service.check_database(session)
