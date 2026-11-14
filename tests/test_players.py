"""Tests for the Player endpoints.

Scenarios covered:
  - Create player (happy path)
  - Create player with duplicate name → 409
  - Create player for a squad that does not exist → 404
  - Create player with empty name → 422
  - List players
  - Get player by id
  - Get player that does not exist → 404
  - Update player name (happy path)
  - Update player with same name → 200 (not a conflict)
  - Update player with duplicate name → 409
  - Update player that does not exist → 404
  - Delete player → 204
  - Delete player that does not exist → 404
"""

import pytest


# ── helpers ───────────────────────────────────────────────────────────────

async def _create_squad(client, name: str) -> dict:
    r = await client.post("/squads", json={"name": name})
    assert r.status_code == 201
    return r.json()


async def _create_player(client, name: str, squad_id: int) -> dict:
    r = await client.post("/players", json={"name": name, "squad_id": squad_id})
    assert r.status_code == 201
    return r.json()


# ── create ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_player_returns_201(client):
    """A new player is created and returned with an id, name, and squad_id."""
    squad = await _create_squad(client, "SquadP1")

    response = await client.post("/players", json={"name": "Carlos", "squad_id": squad["id"]})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Carlos"
    assert data["squad_id"] == squad["id"]
    assert isinstance(data["id"], int)


@pytest.mark.asyncio
async def test_create_player_duplicate_name_returns_409(client):
    """Player names must be globally unique — adding the same name twice is rejected."""
    squad = await _create_squad(client, "SquadP2")
    await _create_player(client, "Diego", squad["id"])

    response = await client.post("/players", json={"name": "Diego", "squad_id": squad["id"]})

    assert response.status_code == 409
    assert "Diego" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_player_squad_not_found_returns_404(client):
    """Creating a player for a non-existent squad returns 404."""
    response = await client.post("/players", json={"name": "Elena", "squad_id": 9999})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_player_empty_name_returns_422(client):
    """Pydantic rejects an empty player name before the service layer is reached."""
    squad = await _create_squad(client, "SquadP3")

    response = await client.post("/players", json={"name": "", "squad_id": squad["id"]})

    assert response.status_code == 422


# ── list ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_players_returns_all(client):
    """GET /players returns every player across all squads."""
    squad = await _create_squad(client, "SquadP4")
    await _create_player(client, "Franco", squad["id"])
    await _create_player(client, "Giulia", squad["id"])

    response = await client.get("/players")

    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert "Franco" in names
    assert "Giulia" in names


@pytest.mark.asyncio
async def test_list_players_empty(client):
    """GET /players returns [] when no players exist."""
    response = await client.get("/players")

    assert response.status_code == 200
    assert response.json() == []


# ── get by id ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_player_by_id(client):
    """GET /players/{id} returns the correct player."""
    squad = await _create_squad(client, "SquadP5")
    player = await _create_player(client, "Hector", squad["id"])

    response = await client.get(f"/players/{player['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Hector"


@pytest.mark.asyncio
async def test_get_player_not_found_returns_404(client):
    """GET /players/9999 returns 404 when the player does not exist."""
    response = await client.get("/players/9999")

    assert response.status_code == 404


# ── update ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_player_name(client):
    """PUT /players/{id} renames a player."""
    squad = await _create_squad(client, "SquadP6")
    player = await _create_player(client, "Ivan", squad["id"])

    response = await client.put(f"/players/{player['id']}", json={"name": "Ivano"})

    assert response.status_code == 200
    assert response.json()["name"] == "Ivano"


@pytest.mark.asyncio
async def test_update_player_same_name_is_allowed(client):
    """Sending the same name in a PUT is not treated as a conflict."""
    squad = await _create_squad(client, "SquadP7")
    player = await _create_player(client, "Julia", squad["id"])

    response = await client.put(f"/players/{player['id']}", json={"name": "Julia"})

    assert response.status_code == 200
    assert response.json()["name"] == "Julia"


@pytest.mark.asyncio
async def test_update_player_duplicate_name_returns_409(client):
    """Renaming a player to a name already in use is rejected."""
    squad = await _create_squad(client, "SquadP8")
    await _create_player(client, "Karl", squad["id"])
    player2 = await _create_player(client, "Leo", squad["id"])

    response = await client.put(f"/players/{player2['id']}", json={"name": "Karl"})

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_player_not_found_returns_404(client):
    """PUT /players/9999 returns 404 when the player does not exist."""
    response = await client.put("/players/9999", json={"name": "Nobody"})

    assert response.status_code == 404


# ── delete ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_player_returns_204(client):
    """DELETE /players/{id} removes the player and returns no content."""
    squad = await _create_squad(client, "SquadP9")
    player = await _create_player(client, "Marco", squad["id"])

    response = await client.delete(f"/players/{player['id']}")

    assert response.status_code == 204
    assert (await client.get(f"/players/{player['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_player_not_found_returns_404(client):
    """DELETE /players/9999 returns 404 when the player does not exist."""
    response = await client.delete("/players/9999")

    assert response.status_code == 404
