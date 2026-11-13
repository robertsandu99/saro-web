FROM python:3.11-slim

# PYTHONDONTWRITEBYTECODE=1 — stops Python writing .pyc bytecode files into the image
# PYTHONUNBUFFERED=1       — forces Python to print logs immediately (no internal buffer delay)
# POETRY_VIRTUALENVS_CREATE=false — tells Poetry NOT to create a venv inside the container
#                                   (the container itself is the isolation, a venv is redundant)
# POETRY_NO_INTERACTION=1  — prevents Poetry from asking any questions during install
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app  
# WORKDIR — all subsequent commands run from this directory inside the container

# Install gcc — needed to compile asyncpg's C extension (asyncpg is partly written in C for speed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*
# rm -rf /var/lib/apt/lists/* — deletes the apt package index after installing
# This shrinks the image size; we don't need the index at runtime

# Install Poetry itself into the container
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"
# --no-cache-dir — don't store pip's download cache; shrinks image size

# ── Dependency install (separate layer for Docker caching) ──────────────────
# Docker builds in layers. By copying only pyproject.toml + poetry.lock FIRST
# and installing deps, Docker caches this layer. If only your source code changes
# (not the dependencies), Docker reuses this cached layer — rebuild is very fast.
COPY pyproject.toml poetry.lock ./

# --only main — install only production deps; skip dev tools (pytest, black, mypy, etc.)
# --no-root   — don't install the saroweb package yet (source isn't copied yet)
RUN poetry install --only main --no-root

# ── Application source ──────────────────────────────────────────────────────
COPY saroweb/ ./saroweb/      
COPY migrations/ ./migrations/ 
COPY alembic.ini ./            

# Now install the saroweb package itself (registers it so 'import saroweb' works)
RUN poetry install --only main

# ── Security: run as non-root user ─────────────────────────────────────────
# By default Docker containers run as root — bad practice.
# If a vulnerability lets someone escape the app, they'd have root on the container.
# Running as 'appuser' limits the blast radius.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
# EXPOSE is documentation only — it tells Docker which port the app listens on.
# The actual port mapping is done in docker-compose.yml (ports: "8080:8080")

# Default command: start uvicorn
# --host 0.0.0.0 — REQUIRED inside Docker. Without this, uvicorn binds to 127.0.0.1
#                  which is only reachable inside the container itself.
#                  0.0.0.0 means "accept connections from any interface" — 
#                  Docker's networking then routes external traffic in correctly.
CMD ["uvicorn", "saroweb.app:app", "--host", "0.0.0.0", "--port", "8080"]
