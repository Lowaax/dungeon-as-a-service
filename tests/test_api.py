import pytest

from tests.conftest import GUERRIER, auth_headers


def create_hero(client, headers, **overrides):
    return client.post("/heroes", json={**GUERRIER, **overrides}, headers=headers)


# --- Palier 1 ---------------------------------------------------------------


def test_create_hero_nominal(client):
    headers = auth_headers(client)
    r = create_hero(client, headers)
    assert r.status_code == 201
    hero = r.json()
    assert hero["salle_actuelle"] == "entree"
    assert hero["pv"] == hero["pv_max"] == 32
    assert hero["en_combat"] is False and hero["est_vivant"] is True
    assert "monstre_pv" not in hero and "owner_id" not in hero


@pytest.mark.parametrize(
    "overrides",
    [
        {"force": 8, "agilite": 5, "intelligence": 2},  # somme 15
        {"nom": "Al"},  # nom trop court
        {"nom": "x" * 21},  # nom trop long
        {"classe": "paladin"},  # classe inconnue
        {"force": 9, "agilite": 0, "intelligence": 1},  # stats hors bornes
    ],
)
def test_create_hero_invalid_422(client, overrides):
    assert create_hero(client, auth_headers(client), **overrides).status_code == 422


def test_unknown_hero_404_structured(client):
    r = client.get("/heroes/9999", headers=auth_headers(client))
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "HERO_NOT_FOUND"


# --- Palier 2 ---------------------------------------------------------------


def test_move_and_no_exit(client):
    headers = auth_headers(client)
    hero_id = create_hero(client, headers).json()["id"]
    r = client.post(f"/heroes/{hero_id}/move", json={"direction": "nord"}, headers=headers)
    assert r.status_code == 200 and r.json()["id"] == "hall"

    r = client.post(f"/heroes/{hero_id}/move", json={"direction": "diagonale"}, headers=headers)
    assert r.status_code == 422

    client.post(f"/heroes/{hero_id}/move", json={"direction": "ouest"}, headers=headers)  # bibliothèque
    client.post(f"/heroes/{hero_id}/attack", headers=headers)  # gobelin vaincu en un coup
    r = client.post(f"/heroes/{hero_id}/move", json={"direction": "nord"}, headers=headers)
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "NO_EXIT"


# --- Palier 3 ---------------------------------------------------------------


def test_combat_gold_rest_and_in_combat(client):
    headers = auth_headers(client)
    hero_id = create_hero(client, headers).json()["id"]
    client.post(f"/heroes/{hero_id}/move", json={"direction": "nord"}, headers=headers)

    r = client.post(f"/heroes/{hero_id}/attack", headers=headers)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "NO_MONSTER"

    room = client.post(f"/heroes/{hero_id}/move", json={"direction": "ouest"}, headers=headers).json()
    assert room["monstre"]["nom"] == "Gobelin" and room["monstre"]["pv"] == 12

    # Impossible de fuir ni de se reposer pendant le combat
    r = client.post(f"/heroes/{hero_id}/move", json={"direction": "est"}, headers=headers)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "IN_COMBAT"
    r = client.post(f"/heroes/{hero_id}/rest", headers=headers)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "IN_COMBAT"

    r = client.post(f"/heroes/{hero_id}/attack", headers=headers).json()
    assert r["degats_infliges"] == 14 and r["issue"] == "monstre_vaincu" and r["or_gagne"] == 10
    assert client.get(f"/heroes/{hero_id}", headers=headers).json()["or_"] == 10

    r = client.post(f"/heroes/{hero_id}/rest", headers=headers)
    assert r.status_code == 200 and r.json()["pv"] == r.json()["pv_max"]


def test_dead_hero_cannot_act_but_is_visible(client):
    headers = auth_headers(client)
    # Guerrier sans force (22 PV, 4 dégâts) : l'ogre (30 PV, 5 dégâts après armure) le tue
    hero_id = create_hero(client, headers, nom="Gimli", force=1, agilite=1, intelligence=8).json()["id"]
    for direction in ["nord", "nord"]:
        client.post(f"/heroes/{hero_id}/move", json={"direction": direction}, headers=headers)
    client.post(f"/heroes/{hero_id}/attack", headers=headers)  # rat géant (8 PV)
    client.post(f"/heroes/{hero_id}/attack", headers=headers)
    client.post(f"/heroes/{hero_id}/move", json={"direction": "nord"}, headers=headers)  # ogre
    issues = [client.post(f"/heroes/{hero_id}/attack", headers=headers).json()["issue"] for _ in range(5)]
    assert issues[-1] == "heros_mort"

    hero = client.get(f"/heroes/{hero_id}", headers=headers)
    assert hero.status_code == 200 and hero.json()["est_vivant"] is False
    for action in ["attack", "rest"]:
        r = client.post(f"/heroes/{hero_id}/{action}", headers=headers)
        assert r.status_code == 409 and r.json()["detail"]["error"] == "HERO_DEAD"
    r = client.post(f"/heroes/{hero_id}/move", json={"direction": "sud"}, headers=headers)
    r = client.post(f"/heroes/{hero_id}/rest", headers=headers)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "HERO_DEAD"


# --- Palier 4 ---------------------------------------------------------------


def test_auth_required_401(client):
    assert client.get("/heroes").status_code == 401
    r = client.get("/heroes", headers={"Authorization": "Bearer pas-un-jwt"})
    assert r.status_code == 401 and r.json()["detail"]["error"] == "INVALID_TOKEN"


def test_bad_password_401(client):
    auth_headers(client)
    r = client.post("/auth/login", data={"username": "alice", "password": "faux"})
    assert r.status_code == 401


def test_other_player_hero_403_and_filtered_list(client):
    alice = auth_headers(client, "alice")
    bob = auth_headers(client, "bob")
    hero_id = create_hero(client, alice).json()["id"]
    r = client.post(f"/heroes/{hero_id}/move", json={"direction": "nord"}, headers=bob)
    assert r.status_code == 403 and r.json()["detail"]["error"] == "NOT_YOUR_HERO"
    assert client.get("/heroes", headers=bob).json() == []
    assert len(client.get("/heroes", headers=alice).json()) == 1


def test_leaderboard_public(client):
    headers = auth_headers(client)
    hero_id = create_hero(client, headers).json()["id"]
    create_hero(client, headers, nom="Boromir")
    client.post(f"/heroes/{hero_id}/move", json={"direction": "nord"}, headers=headers)
    client.post(f"/heroes/{hero_id}/move", json={"direction": "ouest"}, headers=headers)
    client.post(f"/heroes/{hero_id}/attack", headers=headers)
    board = client.get("/leaderboard").json()
    assert [e["nom"] for e in board] == ["Aragorn", "Boromir"]
