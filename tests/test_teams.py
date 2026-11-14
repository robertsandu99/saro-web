"""Tests for the Team generation endpoints.

Scenarios covered:
  - Generate teams (happy path — 15 players into 3 teams)
  - Generate teams — squad not found → 404
  - Generate teams — not enough players → 400
  - Generate teams — team name conflict (same prefix used twice) → 409
  - Generate teams — minimum 2 teams enforced by Pydantic → 422
  - List teams (includes players)
  - Get team by id (includes players)
  - Get team not found → 404
  - Delete team → 204, players still exist
  - Delete team not found → 404
  - Distribution: players are split as evenly as possible
"""

import pytest


# ── helpers ───────────────────────────────────────────────────────────────

async def _create_squad(client, name: str) -> dict:
    r = await client.post("/squads", json={"name": name})
    assert r.status_code == 201
    return r.json()


async def _add_players(client, squad_id: int, names: list[str]) -> list[dict]:
    """Add multiple players to a squad and return their response bodies."""
    players = []
    for name in names:
        r = await client.post("/players", json={"name": name, "squad_id": squad_id})
        assert r.status_code == 201
        players.append(r.json())
    return players


async def _generate(client, squad_id: int, num_teams: int, prefix: str = "Team") -> list[dict]:
    """POST /squads/{id}/generate-teams and return the list of created teams."""
    r = await client.post(
        f"/squads/{squad_id}/generate-teams",
        json={"num_teams": num_teams, "name_prefix": prefix},
    )
    assert r.status_code == 201
    return r.json()


# ── generate — happy path ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_teams_returns_correct_number(client):
    """Generating 3 teams produces exactly 3 team records."""
    squad = await _create_squad(client, "GenSquad1")
    await _add_players(client, squad["id"], [f"Player{i}" for i in range(1, 10)])

    teams = await _generate(client, squad["id"], num_teams=3)

    assert len(teams) == 3


@pytest.mark.asyncio
async def test_generate_teams_names_use_prefix(client):
    """Generated team names follow the pattern '{prefix} 1', '{prefix} 2', etc."""
    squad = await _create_squad(client, "GenSquad2")
    await _add_players(client, squad["id"], [f"P{i}" for i in range(1, 7)])

    teams = await _generate(client, squad["id"], num_teams=2, prefix="Equipo")

    names = {t["name"] for t in teams}
    assert names == {"Equipo 1", "Equipo 2"}


@pytest.mark.asyncio
async def test_generate_teams_every_player_assigned(client):
    """Every player in the squad appears in exactly one team."""
    squad = await _create_squad(client, "GenSquad3")
    players = await _add_players(client, squad["id"], [f"Q{i}" for i in range(1, 10)])
    player_ids = {p["id"] for p in players}

    teams = await _generate(client, squad["id"], num_teams=3)

    # collect all player ids across all teams
    assigned_ids = {p["id"] for t in teams for p in t["players"]}
    assert assigned_ids == player_ids  # every player is assigned, none duplicated


@pytest.mark.asyncio
async def test_generate_teams_15_players_3_teams(client):
    """15 players into 3 teams → each team gets exactly 5 players."""
    squad = await _create_squad(client, "GenSquad4")
    await _add_players(client, squad["id"], [f"R{i}" for i in range(1, 16)])  # 15 players

    teams = await _generate(client, squad["id"], num_teams=3)

    sizes = sorted(t["team_size"] for t in teams)
    assert sizes == [5, 5, 5]  # perfectly divisible


@pytest.mark.asyncio
async def test_generate_teams_uneven_distribution(client):
    """10 players into 3 teams → sizes differ by at most 1 (4, 3, 3)."""
    squad = await _create_squad(client, "GenSquad5")
    await _add_players(client, squad["id"], [f"S{i}" for i in range(1, 11)])  # 10 players

    teams = await _generate(client, squad["id"], num_teams=3)

    sizes = sorted(t["team_size"] for t in teams)
    # 10 / 3 = 3 remainder 1 → one team has 4, two teams have 3
    assert sizes == [3, 3, 4]


@pytest.mark.asyncio
async def test_generated_teams_include_players(client):
    """Each team returned from generate-teams already has its players embedded."""
    squad = await _create_squad(client, "GenSquad6")
    await _add_players(client, squad["id"], [f"T{i}" for i in range(1, 7)])

    teams = await _generate(client, squad["id"], num_teams=2)

    # every team must have at least one player embedded in the response
    for team in teams:
        assert len(team["players"]) > 0


# ── generate — error cases ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_teams_squad_not_found_returns_404(client):
    """Generating teams for a non-existent squad returns 404."""
    response = await client.post(
        "/squads/9999/generate-teams",
        json={"num_teams": 2},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_teams_not_enough_players_returns_400(client):
    """Requesting 3 teams when the squad has only 2 players returns 400."""
    squad = await _create_squad(client, "GenSquad7")
    await _add_players(client, squad["id"], ["Solo1", "Solo2"])  # only 2 players

    response = await client.post(
        f"/squads/{squad['id']}/generate-teams",
        json={"num_teams": 3},  # more teams than players
    )

    # ValidationError → mapped to 400 by AppError handler in app.py
    assert response.status_code == 400
    assert "player" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_teams_name_conflict_returns_409(client):
    """Running generate-teams twice with the same prefix conflicts on team names."""
    squad = await _create_squad(client, "GenSquad8")
    await _add_players(client, squad["id"], [f"U{i}" for i in range(1, 7)])

    # first generation succeeds
    await _generate(client, squad["id"], num_teams=2, prefix="Round")

    # second generation with the same prefix conflicts with "Round 1" and "Round 2"
    response = await client.post(
        f"/squads/{squad['id']}/generate-teams",
        json={"num_teams": 2, "name_prefix": "Round"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_generate_teams_num_teams_less_than_2_returns_422(client):
    """Pydantic rejects num_teams=1 — the Field(ge=2) constraint fires."""
    squad = await _create_squad(client, "GenSquad9")

    response = await client.post(
        f"/squads/{squad['id']}/generate-teams",
        json={"num_teams": 1},
    )

    assert response.status_code == 422


# ── list ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_teams_returns_all(client):
    """GET /teams returns all generated teams."""
    squad = await _create_squad(client, "GenSquad10")
    await _add_players(client, squad["id"], [f"V{i}" for i in range(1, 7)])
    await _generate(client, squad["id"], num_teams=2, prefix="ListTeam")

    response = await client.get("/teams")

    assert response.status_code == 200
    names = [t["name"] for t in response.json()]
    assert "ListTeam 1" in names
    assert "ListTeam 2" in names


# ── get by id ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_team_by_id_includes_players(client):
    """GET /teams/{id} returns the team with its players."""
    squad = await _create_squad(client, "GenSquad11")
    await _add_players(client, squad["id"], [f"W{i}" for i in range(1, 5)])
    teams = await _generate(client, squad["id"], num_teams=2, prefix="GetTeam")

    response = await client.get(f"/teams/{teams[0]['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] in {"GetTeam 1", "GetTeam 2"}
    assert len(data["players"]) > 0  # players are embedded


@pytest.mark.asyncio
async def test_get_team_not_found_returns_404(client):
    """GET /teams/9999 returns 404."""
    response = await client.get("/teams/9999")

    assert response.status_code == 404


# ── delete ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_team_returns_204(client):
    """DELETE /teams/{id} removes the team but NOT the players."""
    squad = await _create_squad(client, "GenSquad12")
    players = await _add_players(client, squad["id"], [f"X{i}" for i in range(1, 5)])
    teams = await _generate(client, squad["id"], num_teams=2, prefix="DelTeam")
    team_id = teams[0]["id"]

    response = await client.delete(f"/teams/{team_id}")

    assert response.status_code == 204
    # team is gone
    assert (await client.get(f"/teams/{team_id}")).status_code == 404
    # but the players still exist in the squad
    for player in players:
        assert (await client.get(f"/players/{player['id']}")).status_code == 200


@pytest.mark.asyncio
async def test_delete_team_not_found_returns_404(client):
    """DELETE /teams/9999 returns 404."""
    response = await client.delete("/teams/9999")

    assert response.status_code == 404
