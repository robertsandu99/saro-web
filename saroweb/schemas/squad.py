from pydantic import BaseModel, ConfigDict, Field

from saroweb.schemas.player import PlayerRead  # used in the "with players" variant


class SquadCreate(BaseModel):
    """Data required to create a new squad."""

    name: str = Field(min_length=1, max_length=100, description="Squad name, must be unique")


class SquadUpdate(BaseModel):
    """Data accepted when renaming an existing squad."""

    name: str = Field(min_length=1, max_length=100, description="New squad name, must be unique")


class SquadRead(BaseModel):
    """Minimal squad response — id and name only."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class SquadReadWithPlayers(SquadRead):
    """Full squad response — includes the list of players in the squad.
    Used by GET /squads/{id} so the caller can see who is in the squad.
    """

    # default=[] means an empty list is returned if no players exist yet
    players: list[PlayerRead] = []
