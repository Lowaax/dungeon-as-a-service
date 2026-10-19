"""BONUS — Client terminal du jeu (argparse + requests).

Exemples :
    python client/play.py register --username alice --password secret
    python client/play.py login --username alice --password secret
    python client/play.py create --name Aragorn --classe guerrier --force 6 --agilite 2 --intelligence 2
    python client/play.py heroes
    python client/play.py look --hero 1
    python client/play.py move --hero 1 --direction nord
    python client/play.py attack --hero 1
    python client/play.py rest --hero 1
    python client/play.py leaderboard

Le token JWT reçu au login est enregistré dans le fichier .token.
"""

import argparse
import os
import sys
from pathlib import Path

import requests

API_URL = os.getenv("DUNGEON_API_URL", "http://127.0.0.1:8000")
TOKEN_FILE = Path(".token")


def load_token() -> str:
    if not TOKEN_FILE.exists():
        sys.exit("Pas de token : connectez-vous d'abord avec la commande login.")
    return TOKEN_FILE.read_text(encoding="utf-8").strip()


def auth() -> dict:
    return {"Authorization": f"Bearer {load_token()}"}


def call(method: str, path: str, **kwargs) -> dict | list:
    try:
        r = requests.request(method, f"{API_URL}{path}", timeout=10, **kwargs)
    except requests.ConnectionError:
        sys.exit(f"Impossible de joindre l'API sur {API_URL}. Le serveur est-il lancé ?")
    if r.status_code >= 400:
        detail = r.json().get("detail")
        if isinstance(detail, dict):
            sys.exit(f"Erreur {r.status_code} [{detail['error']}] : {detail['message']}")
        sys.exit(f"Erreur {r.status_code} : {detail}")
    return r.json()


def print_hero(h: dict) -> None:
    etat = "mort" if not h["est_vivant"] else ("en combat" if h["en_combat"] else "libre")
    trophee = " — VAINQUEUR DE LA LICHE" if h["victoire"] else ""
    print(
        f"#{h['id']} {h['nom']} ({h['classe']}) — PV {h['pv']}/{h['pv_max']} — "
        f"{h['or_']} or — salle : {h['salle_actuelle']} — {etat}{trophee}"
    )


def print_room(room: dict) -> None:
    print(f"\n== {room['nom']} ==")
    print(room["description"])
    sorties = ", ".join(f"{d} -> {s}" for d, s in room["sorties"].items())
    print(f"Sorties : {sorties}")
    if room["monstre"]:
        m = room["monstre"]
        print(f"!! {m['nom']} vous attaque ({m['pv']}/{m['pv_max']} PV, attaque {m['attaque']})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dungeon as a Service — client terminal")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health", help="Vérifie que l'API répond")
    for name in ("register", "login"):
        p = sub.add_parser(name, help="Créer un compte" if name == "register" else "Se connecter")
        p.add_argument("--username", required=True)
        p.add_argument("--password", required=True)

    p = sub.add_parser("create", help="Créer un héros")
    p.add_argument("--name", required=True)
    p.add_argument("--classe", required=True, choices=["guerrier", "mage", "voleur"])
    p.add_argument("--force", type=int, required=True)
    p.add_argument("--agilite", type=int, required=True)
    p.add_argument("--intelligence", type=int, required=True)

    sub.add_parser("heroes", help="Lister mes héros")
    for name, aide in (("look", "Décrire la salle"), ("attack", "Attaquer le monstre"), ("rest", "Se reposer (3 s)")):
        sub.add_parser(name, help=aide).add_argument("--hero", type=int, required=True)
    p = sub.add_parser("move", help="Se déplacer")
    p.add_argument("--hero", type=int, required=True)
    p.add_argument("--direction", required=True, choices=["nord", "sud", "est", "ouest"])
    sub.add_parser("leaderboard", help="Afficher le classement")

    args = parser.parse_args()

    match args.command:
        case "health":
            print(call("GET", "/health")["message"])
        case "register":
            player = call("POST", "/auth/register", json={"username": args.username, "password": args.password})
            print(f"Compte créé : {player['username']} (#{player['id']})")
        case "login":
            token = call("POST", "/auth/login", data={"username": args.username, "password": args.password})
            TOKEN_FILE.write_text(token["access_token"], encoding="utf-8")
            print(f"Connecté en tant que {args.username}. Token enregistré dans {TOKEN_FILE}.")
        case "create":
            body = {
                "nom": args.name, "classe": args.classe, "force": args.force,
                "agilite": args.agilite, "intelligence": args.intelligence,
            }
            print_hero(call("POST", "/heroes", json=body, headers=auth()))
        case "heroes":
            heroes = call("GET", "/heroes", headers=auth())
            for h in heroes:
                print_hero(h)
            if not heroes:
                print("Aucun héros. Créez-en un avec la commande create.")
        case "look":
            print_room(call("GET", f"/heroes/{args.hero}/room", headers=auth()))
        case "move":
            print_room(call("POST", f"/heroes/{args.hero}/move", json={"direction": args.direction}, headers=auth()))
        case "attack":
            t = call("POST", f"/heroes/{args.hero}/attack", headers=auth())
            crit = " COUP CRITIQUE !" if t["critique"] else ""
            print(f"Vous infligez {t['degats_infliges']} dégâts.{crit} Le monstre a {t['pv_monstre']} PV.")
            if t["degats_subis"]:
                print(f"Le monstre riposte : {t['degats_subis']} dégâts. Il vous reste {t['pv_heros']} PV.")
            if t["issue"] == "monstre_vaincu":
                print(f"Monstre vaincu ! +{t['or_gagne']} or.")
            elif t["issue"] == "heros_mort":
                print("Vous êtes mort... Votre aventure s'arrête ici.")
            if t["victoire"] and t["issue"] == "monstre_vaincu":
                print("*** La Liche est vaincue ! Vous avez triomphé du donjon ! ***")
        case "rest":
            print("Vous vous reposez...")
            print_hero(call("POST", f"/heroes/{args.hero}/rest", headers=auth()))
        case "leaderboard":
            for e in call("GET", "/leaderboard"):
                star = "★" if e["victoire"] else " "
                print(f"{e['rang']:>2}. {star} {e['nom']} ({e['classe']}, {e['joueur']}) — {e['or_']} or")


if __name__ == "__main__":
    main()
