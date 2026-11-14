from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from saroweb.database import Base


class Player(Base):
    """A person in a squad. Skill and position attributes will be added later."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)

    # player names are globally unique for now;
    # once User is added this will become unique per user
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # every player belongs to exactly one squad
    # ForeignKey("squads.id") creates a database foreign key constraint
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id"), nullable=False)

    # back_populates links the two sides of the relationship so SQLAlchemy
    # keeps them in sync — squad.players and player.squad refer to each other
    squad: Mapped["Squad"] = relationship("Squad", back_populates="players")
