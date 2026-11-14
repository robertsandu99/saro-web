from pydantic import BaseModel, ConfigDict, Field


class PlayerCreate(BaseModel):
    """Data required to create a new player."""

    name: str = Field(min_length=1, max_length=100, description="Player name, must be unique")
    squad_id: int = Field(description="ID of the squad this player belongs to")


class PlayerUpdate(BaseModel):
    """Data accepted when renaming an existing player."""

    name: str = Field(min_length=1, max_length=100, description="New player name, must be unique")


class PlayerRead(BaseModel):
    """Shape of a player returned in API responses."""

    id: int
    name: str
    squad_id: int

    # from_attributes=True allows Pydantic to read values from SQLAlchemy ORM objects
    # (ORM objects have attributes like player.name, not dict keys like {"name": ...})
    model_config = ConfigDict(from_attributes=True)
