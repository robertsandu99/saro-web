# Import all models here so SQLAlchemy's Base.metadata knows about them.
# Without these imports, Alembic autogenerate would see no models and generate empty migrations.
# noqa: F401 silences the "imported but unused" linter warning — the import is intentional
from saroweb.models.player import Player  # noqa: F401
from saroweb.models.squad import Squad    # noqa: F401
from saroweb.models.team import Team      # noqa: F401
