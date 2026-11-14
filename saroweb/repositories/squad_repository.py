from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from saroweb.models.squad import Squad


async def get_by_id(session: AsyncSession, squad_id: int) -> Squad | None:
    """Return the squad with the given id, or None if it doesn't exist."""
    result = await session.execute(select(Squad).where(Squad.id == squad_id))
    return result.scalar_one_or_none()


async def get_by_id_with_players(session: AsyncSession, squad_id: int) -> Squad | None:
    """Return the squad with its players eagerly loaded.

    selectinload runs a second SELECT query to load players in one go,
    avoiding the N+1 problem (one query per player).
    """
    result = await session.execute(
        select(Squad)
        .where(Squad.id == squad_id)
        .options(selectinload(Squad.players))
    )
    return result.scalar_one_or_none()


async def get_by_name(session: AsyncSession, name: str) -> Squad | None:
    """Return the squad with this name, or None — used for duplicate-name checks."""
    result = await session.execute(select(Squad).where(Squad.name == name))
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession) -> list[Squad]:
    """Return every squad (without players — list view only needs names)."""
    result = await session.execute(select(Squad))
    return list(result.scalars().all())


async def create(session: AsyncSession, name: str) -> Squad:
    """Insert a new squad row and return it with its generated id."""
    squad = Squad(name=name)
    session.add(squad)
    # flush sends the INSERT to the database inside the current transaction
    # but does NOT commit — the caller decides when to commit
    await session.flush()
    return squad


async def update(session: AsyncSession, squad: Squad, name: str) -> Squad:
    """Rename an existing squad."""
    squad.name = name
    await session.flush()
    return squad


async def delete(session: AsyncSession, squad: Squad) -> None:
    """Delete a squad (cascades to its players and teams via the ORM relationship)."""
    await session.delete(squad)
    await session.flush()
