from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.database import get_session
from saroweb.schemas.squad import SquadCreate, SquadRead, SquadReadWithPlayers, SquadUpdate
from saroweb.services import squad_service

# prefix="/squads" means all routes in this file start with /squads
# tags=["Squads"] groups these routes together in the Swagger UI (/docs)
router = APIRouter(prefix="/squads", tags=["Squads"])


@router.post("", response_model=SquadRead, status_code=status.HTTP_201_CREATED)
async def create_squad(
    body: SquadCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new squad. Name must be unique."""
    return await squad_service.create(session, body.name)


@router.get("", response_model=list[SquadRead])
async def list_squads(session: AsyncSession = Depends(get_session)):
    """List all squads (without player details)."""
    return await squad_service.get_all(session)


@router.get("/{squad_id}", response_model=SquadReadWithPlayers)
async def get_squad(squad_id: int, session: AsyncSession = Depends(get_session)):
    """Get a squad by id, including all players in it."""
    return await squad_service.get_by_id(session, squad_id)


@router.put("/{squad_id}", response_model=SquadRead)
async def update_squad(
    squad_id: int,
    body: SquadUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Rename a squad. New name must be unique."""
    return await squad_service.update(session, squad_id, body.name)


@router.delete("/{squad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_squad(squad_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a squad and all its players and teams."""
    await squad_service.delete(session, squad_id)
