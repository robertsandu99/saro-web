from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from saroweb.database import Base


class Squad(Base):
    """A named collection of players that belongs to a user (user added later)."""

    __tablename__ = "squads"

    # primary key — SQLAlchemy generates an auto-incrementing integer id
    id: Mapped[int] = mapped_column(primary_key=True)

    # unique=True enforces the uniqueness constraint at the database level
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # one squad → many players
    # cascade="all, delete-orphan" means: when this squad is deleted,
    # automatically delete all its players too — no orphan rows left in the DB
    players: Mapped[list["Player"]] = relationship(
        "Player", back_populates="squad", cascade="all, delete-orphan"
    )

    # one squad → many generated teams
    teams: Mapped[list["Team"]] = relationship(
        "Team", back_populates="squad", cascade="all, delete-orphan"
    )
