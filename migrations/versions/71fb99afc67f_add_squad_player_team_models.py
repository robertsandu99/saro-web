"""Add squad, player and team models.

Revision ID: 71fb99afc67f
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers used by Alembic to track migration history
revision = "71fb99afc67f"
down_revision = None   # None means this is the first migration (no parent)
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the squads, players, teams and team_players tables."""

    # squads — a named collection of players
    op.create_table(
        "squads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # players — a person belonging to exactly one squad
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("squad_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["squad_id"], ["squads.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # teams — a generated group of players from a squad
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("team_size", sa.Integer(), nullable=False),
        sa.Column("squad_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["squad_id"], ["squads.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # team_players — many-to-many bridge between teams and players
    op.create_table(
        "team_players",
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        # ondelete="CASCADE" keeps the bridge table clean when a team or player is deleted
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "player_id"),
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    # team_players must go first because it references teams and players
    op.drop_table("team_players")
    op.drop_table("teams")
    op.drop_table("players")
    op.drop_table("squads")
