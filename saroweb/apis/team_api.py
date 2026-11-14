from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from saroweb.database import get_session
from saroweb.schemas.team import GenerateTeamsRequest, TeamRead
from saroweb.services import team_service

# No global prefix — this router has two different URL shapes:
#   POST /squads/{id}/generate-teams  (nested under squads)
#   GET/DELETE /teams/{id}            (top-level)
router = APIRouter(tags=["Teams"])


@router.post(
    "/squads/{squad_id}/generate-teams",
    response_model=list[TeamRead],
    status_code=status.HTTP_201_CREATED,
)
async def generate_teams(
    squad_id: int,
    body: GenerateTeamsRequest,
    session: AsyncSession = Depends(get_session),
):
    """Generate balanced teams from the players in a squad.

    Example: squad has 15 players, num_teams=3 → three teams of 5.
    Players are distributed randomly (skill-based balancing comes in a later step).
    """
    return await team_service.generate_teams(session, squad_id, body.num_teams, body.name_prefix)


@router.get("/teams", response_model=list[TeamRead])
async def list_teams(session: AsyncSession = Depends(get_session)):
    """List all generated teams with their players."""
    return await team_service.get_all(session)


@router.get("/teams/{team_id}", response_model=TeamRead)
async def get_team(team_id: int, session: AsyncSession = Depends(get_session)):
    """Get a single team with its players."""
    return await team_service.get_by_id(session, team_id)


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a team. The players themselves are not deleted."""
    await team_service.delete(session, team_id)
