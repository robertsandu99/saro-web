from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from saroweb.models.player import Player
from saroweb.models.team import Team


async def get_by_id(session: AsyncSession, team_id: int) -> Team | None:
    """Return team by id without players loaded."""
    result = await session.execute(select(Team).where(Team.id == team_id))
    return result.scalar_one_or_none()


async def get_by_id_with_players(session: AsyncSession, team_id: int) -> Team | None:
    """Return team with its players eagerly loaded."""
    result = await session.execute(
        select(Team)
        .where(Team.id == team_id)
        .options(selectinload(Team.players))
    )
    return result.scalar_one_or_none()


async def get_by_name(session: AsyncSession, name: str) -> Team | None:
    """Return team by name, or None — used for duplicate-name checks."""
    result = await session.execute(select(Team).where(Team.name == name))
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession) -> list[Team]:
    """Return all teams with their players eagerly loaded."""
    result = await session.execute(
        select(Team).options(selectinload(Team.players))
    )
    return list(result.scalars().all())


async def create_with_players(
    session: AsyncSession,
    name: str,
    squad_id: int,
    players: list[Player],
) -> Team:
    """Create a team and assign the given players to it in one step.

    team_size is derived from the actual number of players assigned,
    not from a user input — this ensures team_size is always accurate.
    """
    team = Team(
        name=name,
        squad_id=squad_id,
        team_size=len(players),
        players=players,  # SQLAlchemy handles writing to team_players automatically
    )
    session.add(team)
    await session.flush()
    return team


async def delete(session: AsyncSession, team: Team) -> None:
    """Delete a team (team_players rows are removed by ondelete=CASCADE)."""
    await session.delete(team)
    await session.flush()
