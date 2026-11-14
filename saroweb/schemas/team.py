from pydantic import BaseModel, ConfigDict, Field

from saroweb.schemas.player import PlayerRead


class GenerateTeamsRequest(BaseModel):
    """Body sent to POST /squads/{id}/generate-teams."""

    # ge=2 — Pydantic rejects any value less than 2 (need at least 2 teams)
    num_teams: int = Field(ge=2, description="How many teams to create (minimum 2)")

    # the generated teams are named '{name_prefix} 1', '{name_prefix} 2', etc.
    name_prefix: str = Field(
        default="Team",
        min_length=1,
        max_length=50,
        description="Prefix for generated team names, e.g. 'Team' → 'Team 1', 'Team 2'",
    )


class TeamRead(BaseModel):
    """Shape of a team returned in API responses, including its players."""

    id: int
    name: str
    team_size: int   # number of players assigned to this team
    squad_id: int
    players: list[PlayerRead] = []

    model_config = ConfigDict(from_attributes=True)
