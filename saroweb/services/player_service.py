from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.repositories import player_repository, squad_repository
from saroweb.utils.exceptions import ConflictError, NotFoundError


async def create(session: AsyncSession, name: str, squad_id: int):
    """Add a player to a squad, validating both name uniqueness and squad existence."""
    # make sure the squad exists before adding a player to it
    if not await squad_repository.get_by_id(session, squad_id):
        raise NotFoundError(f"Squad {squad_id} not found")

    if await player_repository.get_by_name(session, name):
        raise ConflictError(f"Player '{name}' already exists")

    player = await player_repository.create(session, name, squad_id)
    await session.commit()
    return player


async def get_all(session: AsyncSession):
    """Return all players across all squads."""
    return await player_repository.get_all(session)


async def get_by_id(session: AsyncSession, player_id: int):
    """Return a player by id, or raise 404."""
    player = await player_repository.get_by_id(session, player_id)
    if not player:
        raise NotFoundError(f"Player {player_id} not found")
    return player


async def update(session: AsyncSession, player_id: int, name: str):
    """Rename a player, checking that the new name is not already taken."""
    player = await player_repository.get_by_id(session, player_id)
    if not player:
        raise NotFoundError(f"Player {player_id} not found")

    # skip the conflict check if the caller sent the same name — not an error
    if name != player.name and await player_repository.get_by_name(session, name):
        raise ConflictError(f"Player '{name}' already exists")

    player = await player_repository.update(session, player, name)
    await session.commit()
    return player


async def delete(session: AsyncSession, player_id: int) -> None:
    """Delete a player (removes them from any teams they were in via DB cascade)."""
    player = await player_repository.get_by_id(session, player_id)
    if not player:
        raise NotFoundError(f"Player {player_id} not found")

    await player_repository.delete(session, player)
    await session.commit()
