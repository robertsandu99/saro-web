from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.repositories import squad_repository
from saroweb.utils.exceptions import ConflictError, NotFoundError


async def create(session: AsyncSession, name: str):
    """Create a new squad, rejecting duplicate names."""
    # check for a name conflict before inserting
    if await squad_repository.get_by_name(session, name):
        raise ConflictError(f"Squad '{name}' already exists")

    squad = await squad_repository.create(session, name)
    await session.commit()  # commit makes the change permanent in the database
    return squad


async def get_all(session: AsyncSession):
    """Return all squads (name + id only, no players)."""
    return await squad_repository.get_all(session)


async def get_by_id(session: AsyncSession, squad_id: int):
    """Return a squad with its players, or raise 404 if it doesn't exist."""
    squad = await squad_repository.get_by_id_with_players(session, squad_id)
    if not squad:
        raise NotFoundError(f"Squad {squad_id} not found")
    return squad


async def update(session: AsyncSession, squad_id: int, name: str):
    """Rename a squad, checking that the new name is not already taken."""
    squad = await squad_repository.get_by_id(session, squad_id)
    if not squad:
        raise NotFoundError(f"Squad {squad_id} not found")

    # skip the conflict check if the name hasn't changed
    if name != squad.name and await squad_repository.get_by_name(session, name):
        raise ConflictError(f"Squad '{name}' already exists")

    squad = await squad_repository.update(session, squad, name)
    await session.commit()
    return squad


async def delete(session: AsyncSession, squad_id: int) -> None:
    """Delete a squad and all its players and teams (cascade)."""
    squad = await squad_repository.get_by_id(session, squad_id)
    if not squad:
        raise NotFoundError(f"Squad {squad_id} not found")

    await squad_repository.delete(session, squad)
    await session.commit()
