from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.models.player import Player


async def get_by_id(session: AsyncSession, player_id: int) -> Player | None:
    """Return the player with the given id, or None."""
    result = await session.execute(select(Player).where(Player.id == player_id))
    return result.scalar_one_or_none()


async def get_by_name(session: AsyncSession, name: str) -> Player | None:
    """Return the player with this name, or None — used for duplicate-name checks."""
    result = await session.execute(select(Player).where(Player.name == name))
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession) -> list[Player]:
    """Return every player across all squads."""
    result = await session.execute(select(Player))
    return list(result.scalars().all())


async def get_by_squad(session: AsyncSession, squad_id: int) -> list[Player]:
    """Return all players that belong to a specific squad."""
    result = await session.execute(select(Player).where(Player.squad_id == squad_id))
    return list(result.scalars().all())


async def create(session: AsyncSession, name: str, squad_id: int) -> Player:
    """Insert a new player and return it with its generated id."""
    player = Player(name=name, squad_id=squad_id)
    session.add(player)
    await session.flush()
    return player


async def update(session: AsyncSession, player: Player, name: str) -> Player:
    """Rename an existing player."""
    player.name = name
    await session.flush()
    return player


async def delete(session: AsyncSession, player: Player) -> None:
    """Delete a player (the ondelete=CASCADE in team_players removes them from teams too)."""
    await session.delete(player)
    await session.flush()
