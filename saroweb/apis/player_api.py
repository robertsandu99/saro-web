from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.database import get_session
from saroweb.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate
from saroweb.services import player_service

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("", response_model=PlayerRead, status_code=status.HTTP_201_CREATED)
async def create_player(
    body: PlayerCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new player and assign them to a squad. Name must be unique."""
    return await player_service.create(session, body.name, body.squad_id)


@router.get("", response_model=list[PlayerRead])
async def list_players(session: AsyncSession = Depends(get_session)):
    """List all players across all squads."""
    return await player_service.get_all(session)


@router.get("/{player_id}", response_model=PlayerRead)
async def get_player(player_id: int, session: AsyncSession = Depends(get_session)):
    """Get a single player by id."""
    return await player_service.get_by_id(session, player_id)


@router.put("/{player_id}", response_model=PlayerRead)
async def update_player(
    player_id: int,
    body: PlayerUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Rename a player. New name must be unique."""
    return await player_service.update(session, player_id, body.name)


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(player_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a player. They will be removed from any teams they were in."""
    await player_service.delete(session, player_id)
