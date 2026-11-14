from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from saroweb.database import Base

# team_players is an association table — it represents the many-to-many link
# between teams and players. It has no class of its own, just two foreign keys.
# Example row: team_id=3, player_id=7  → player 7 is in team 3
team_players = Table(
    "team_players",
    Base.metadata,
    Column(
        "team_id",
        Integer,
        # ondelete="CASCADE" — when a team row is deleted,
        # automatically delete its rows in this table too
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "player_id",
        Integer,
        # same cascade: when a player is deleted, remove them from all teams
        ForeignKey("players.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Team(Base):
    """A group of players generated from a squad."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)

    # team names must be unique — prevents duplicate team names per generation run
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # how many players were assigned when the team was generated
    team_size: Mapped[int] = mapped_column(nullable=False)

    # which squad this team was generated from
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id"), nullable=False)

    squad: Mapped["Squad"] = relationship("Squad", back_populates="teams")

    # secondary= tells SQLAlchemy to use the team_players table as the bridge
    # so team.players gives you the list of Player objects in this team
    players: Mapped[list["Player"]] = relationship("Player", secondary=team_players)
