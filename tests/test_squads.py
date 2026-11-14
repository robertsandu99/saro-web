"""Tests for the Squad endpoints.

Scenarios covered:
  - Create squad (happy path)
  - Create squad with duplicate name → 409
  - Create squad with empty name → 422 (Pydantic rejects it before the service runs)
  - List squads
  - Get squad by id (includes players)
  - Get squad that does not exist → 404
  - Update squad name (happy path)
  - Update squad with duplicate name → 409
  - Update squad that does not exist → 404
  - Delete squad → 204
  - Delete squad that does not exist → 404
  - Delete squad cascades its players (players are removed too)
"""

import pytest


# ── helpers ───────────────────────────────────────────────────────────────

async def _create_squad(client, name: str) -> dict:
    """Shortcut: POST /squads and return the response body."""
    response = await client.post("/squads", json={"name": name})
    assert response.status_code == 201
    return response.json()


# ── create ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_squad_returns_201_with_data(client):
    """A new squad is created and returned with an id and the given name."""
    response = await client.post("/squads", json={"name": "Alpha"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alpha"
    assert isinstance(data["id"], int)  # id was assigned by the database


@pytest.mark.asyncio
async def test_create_squad_duplicate_name_returns_409(client):
    """Creating two squads with the same name is rejected with 409 Conflict."""
    await _create_squad(client, "Beta")

    response = await client.post("/squads", json={"name": "Beta"})

    assert response.status_code == 409
    assert "Beta" in response.json()["detail"]  # error message names the conflicting value


@pytest.mark.asyncio
async def test_create_squad_empty_name_returns_422(client):
    """Pydantic rejects an empty name before it reaches the service layer."""
    response = await client.post("/squads", json={"name": ""})

    # 422 Unprocessable Entity — Pydantic validation failure
    assert response.status_code == 422


# ── list ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_squads_returns_all(client):
    """GET /squads returns a list of all squads."""
    await _create_squad(client, "Squad A")
    await _create_squad(client, "Squad B")

    response = await client.get("/squads")

    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert "Squad A" in names
    assert "Squad B" in names


@pytest.mark.asyncio
async def test_list_squads_empty_returns_empty_list(client):
    """GET /squads returns [] when no squads exist."""
    response = await client.get("/squads")

    assert response.status_code == 200
    assert response.json() == []


# ── get by id ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_squad_by_id_includes_players(client):
    """GET /squads/{id} returns the squad with its player list embedded."""
    squad = await _create_squad(client, "Gamma")
    # add two players to the squad
    await client.post("/players", json={"name": "Alice", "squad_id": squad["id"]})
    await client.post("/players", json={"name": "Bob", "squad_id": squad["id"]})

    response = await client.get(f"/squads/{squad['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Gamma"
    player_names = [p["name"] for p in data["players"]]
    assert "Alice" in player_names
    assert "Bob" in player_names


@pytest.mark.asyncio
async def test_get_squad_not_found_returns_404(client):
    """GET /squads/9999 returns 404 when the squad does not exist."""
    response = await client.get("/squads/9999")

    assert response.status_code == 404


# ── update ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_squad_name(client):
    """PUT /squads/{id} renames a squad successfully."""
    squad = await _create_squad(client, "Old Name")

    response = await client.put(f"/squads/{squad['id']}", json={"name": "New Name"})

    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_update_squad_same_name_is_allowed(client):
    """Sending the same name in a PUT is not a conflict — it is a no-op rename."""
    squad = await _create_squad(client, "Same")

    response = await client.put(f"/squads/{squad['id']}", json={"name": "Same"})

    assert response.status_code == 200
    assert response.json()["name"] == "Same"


@pytest.mark.asyncio
async def test_update_squad_duplicate_name_returns_409(client):
    """Renaming a squad to an already-used name is rejected."""
    await _create_squad(client, "Taken")
    squad = await _create_squad(client, "Free")

    response = await client.put(f"/squads/{squad['id']}", json={"name": "Taken"})

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_squad_not_found_returns_404(client):
    """PUT /squads/9999 returns 404 when the squad does not exist."""
    response = await client.put("/squads/9999", json={"name": "Whatever"})

    assert response.status_code == 404


# ── delete ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_squad_returns_204(client):
    """DELETE /squads/{id} removes the squad and returns no content."""
    squad = await _create_squad(client, "ToDelete")

    response = await client.delete(f"/squads/{squad['id']}")

    assert response.status_code == 204
    # verify it is actually gone
    assert (await client.get(f"/squads/{squad['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_squad_not_found_returns_404(client):
    """DELETE /squads/9999 returns 404 when the squad does not exist."""
    response = await client.delete("/squads/9999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_squad_cascades_players(client):
    """Deleting a squad also deletes all players that belonged to it."""
    squad = await _create_squad(client, "WithPlayers")
    r = await client.post("/players", json={"name": "CascadePlayer", "squad_id": squad["id"]})
    player_id = r.json()["id"]

    await client.delete(f"/squads/{squad['id']}")

    # the player should no longer exist
    assert (await client.get(f"/players/{player_id}")).status_code == 404
