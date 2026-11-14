import random

from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.repositories import player_repository, squad_repository, team_repository
from saroweb.utils.exceptions import ConflictError, NotFoundError, ValidationError


async def generate_teams(
    session: AsyncSession,
    squad_id: int,
    num_teams: int,
    name_prefix: str,
) -> list:
    """Split a squad's players into num_teams balanced groups and persist them.

    Current balancing strategy: random shuffle + round-robin distribution.
    When player skill is added in a future step, this will switch to a
    snake-draft algorithm (best player → team 1, second best → team 2, ...,
    then reverse direction) which produces the most balanced result.
    """
    # verify the squad exists
    squad = await squad_repository.get_by_id(session, squad_id)
    if not squad:
        raise NotFoundError(f"Squad {squad_id} not found")

    players = await player_repository.get_by_squad(session, squad_id)

    # need at least one player per team
    if len(players) < num_teams:
        raise ValidationError(
            f"Squad has {len(players)} player(s) but {num_teams} teams were requested. "
            f"Add more players or reduce the number of teams."
        )

    # generate team names and check for conflicts before creating anything
    # this avoids a partial state where some teams were created but then a conflict was hit
    team_names = [f"{name_prefix} {i + 1}" for i in range(num_teams)]
    for name in team_names:
        if await team_repository.get_by_name(session, name):
            raise ConflictError(
                f"A team named '{name}' already exists. "
                f"Use a different name_prefix or delete the existing teams first."
            )

    # shuffle for fairness — without skill data, random order is the best we can do
    shuffled = list(players)
    random.shuffle(shuffled)

    # round-robin distribution: player 0 → team 0, player 1 → team 1, ...
    # player num_teams → team 0 again, and so on
    # this guarantees teams differ by at most 1 player when players don't divide evenly
    groups: list[list] = [[] for _ in range(num_teams)]
    for i, player in enumerate(shuffled):
        groups[i % num_teams].append(player)

    # create a Team record for each group
    teams = []
    for name, group in zip(team_names, groups):
        team = await team_repository.create_with_players(session, name, squad_id, group)
        teams.append(team)

    await session.commit()
    return teams


async def get_all(session: AsyncSession):
    """Return all teams with their players."""
    return await team_repository.get_all(session)


async def get_by_id(session: AsyncSession, team_id: int):
    """Return a team with its players, or raise 404."""
    team = await team_repository.get_by_id_with_players(session, team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")
    return team


async def delete(session: AsyncSession, team_id: int) -> None:
    """Delete a team (players themselves are not deleted, only the assignment)."""
    team = await team_repository.get_by_id(session, team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    await team_repository.delete(session, team)
    await session.commit()
