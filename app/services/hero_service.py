"""Logique du jeu : création, exploration, combat et repos des héros."""

import asyncio
import logging

from sqlmodel import Session, col, select

from app.domain.heros import creer_heros
from app.models.hero import Hero
from app.models.player import Player
from app.schemas.hero import AttackResult, HeroCreate, LeaderboardEntry, MonsterRead, RoomRead
from app.services import errors
from app.services.dungeon_map import FINAL_ROOM, START_ROOM, get_monster_of_room, get_room

logger = logging.getLogger("dungeon")

REST_DURATION_SECONDS = 3


# --- Consultation -----------------------------------------------------------


def create_hero(session: Session, data: HeroCreate, owner: Player) -> Hero:
    heros = creer_heros(data.classe.value, data.force, data.agilite, data.intelligence)
    hero = Hero(
        nom=data.nom,
        classe=data.classe.value,
        force=data.force,
        agilite=data.agilite,
        intelligence=data.intelligence,
        pv=heros.pv_max,
        pv_max=heros.pv_max,
        salle_actuelle=START_ROOM,
        owner_id=owner.id,
    )
    session.add(hero)
    session.commit()
    session.refresh(hero)
    logger.info("Création : %s le %s (#%s) entre dans le donjon", hero.nom, hero.classe, hero.id)
    return hero


def list_heroes(session: Session, owner: Player) -> list[Hero]:
    return list(session.exec(select(Hero).where(Hero.owner_id == owner.id)).all())


def get_hero(session: Session, hero_id: int, player: Player) -> Hero:
    hero = session.get(Hero, hero_id)
    if hero is None:
        raise errors.hero_not_found(hero_id)
    if hero.owner_id != player.id:
        raise errors.not_your_hero()
    return hero


def describe_room(hero: Hero) -> RoomRead:
    room = get_room(hero.salle_actuelle)
    monstre = None
    if hero.monstre_pv is not None:
        modele = get_monster_of_room(hero.salle_actuelle)
        monstre = MonsterRead(
            nom=modele["name"], pv=hero.monstre_pv, pv_max=modele["hp"], attaque=modele["attack"]
        )
    return RoomRead(
        id=hero.salle_actuelle,
        nom=room["name"],
        description=room["description"],
        sorties=room["exits"],
        monstre=monstre,
    )


# --- Actions ----------------------------------------------------------------


def _ensure_alive(hero: Hero) -> None:
    if hero.pv <= 0:
        raise errors.hero_dead()


def move(session: Session, hero: Hero, direction: str) -> RoomRead:
    _ensure_alive(hero)
    if hero.monstre_pv is not None:
        raise errors.in_combat()

    exits = get_room(hero.salle_actuelle)["exits"]
    if direction not in exits:
        raise errors.no_exit(direction)

    hero.salle_actuelle = exits[direction]
    # Donjon maudit : le monstre réapparaît, PV au maximum, à chaque entrée
    monstre = get_monster_of_room(hero.salle_actuelle)
    hero.monstre_pv = monstre["hp"] if monstre else None
    session.add(hero)
    session.commit()
    session.refresh(hero)

    logger.info("Déplacement : %s (#%s) va vers le %s -> %s", hero.nom, hero.id, direction, hero.salle_actuelle)
    if monstre:
        logger.info("Combat : %s surgit face à %s (%s PV)", monstre["name"], hero.nom, monstre["hp"])
    return describe_room(hero)


def attack(session: Session, hero: Hero) -> AttackResult:
    _ensure_alive(hero)
    if hero.monstre_pv is None:
        raise errors.no_monster()

    monstre = get_monster_of_room(hero.salle_actuelle)
    heros = creer_heros(hero.classe, hero.force, hero.agilite, hero.intelligence)

    # 1. Le héros frappe en premier
    degats_infliges, critique = heros.calculer_degats()
    pv_monstre = max(0, hero.monstre_pv - degats_infliges)
    degats_subis = 0
    or_gagne = 0

    if pv_monstre == 0:
        issue = "monstre_vaincu"
        hero.monstre_pv = None
        or_gagne = monstre["gold"]
        hero.or_ += or_gagne
        if hero.salle_actuelle == FINAL_ROOM:
            hero.victoire = True
            logger.info("Victoire : %s a vaincu %s !", hero.nom, monstre["name"])
    else:
        # 2. Le monstre survit : il riposte
        hero.monstre_pv = pv_monstre
        degats_subis = heros.subir_degats(monstre["attack"])
        hero.pv = max(0, hero.pv - degats_subis)
        issue = "heros_mort" if hero.pv == 0 else "en_cours"

    session.add(hero)
    session.commit()
    session.refresh(hero)

    logger.info(
        "Combat : %s inflige %s%s à %s (%s PV restants), subit %s (%s PV) -> %s",
        hero.nom, degats_infliges, " (critique)" if critique else "", monstre["name"],
        pv_monstre, degats_subis, hero.pv, issue,
    )
    return AttackResult(
        degats_infliges=degats_infliges,
        critique=critique,
        degats_subis=degats_subis,
        pv_heros=hero.pv,
        pv_monstre=pv_monstre,
        issue=issue,
        or_gagne=or_gagne,
        victoire=hero.victoire,
    )


async def rest(session: Session, hero: Hero) -> Hero:
    _ensure_alive(hero)
    if hero.monstre_pv is not None:
        raise errors.in_combat()

    logger.info("Repos : %s (#%s) se repose %ss", hero.nom, hero.id, REST_DURATION_SECONDS)
    # Non bloquant : le serveur continue de répondre pendant le repos
    await asyncio.sleep(REST_DURATION_SECONDS)

    hero.pv = hero.pv_max
    session.add(hero)
    session.commit()
    session.refresh(hero)
    logger.info("Repos : %s a récupéré tous ses PV (%s)", hero.nom, hero.pv)
    return hero


# --- Classement -------------------------------------------------------------


def leaderboard(session: Session, limit: int = 10) -> list[LeaderboardEntry]:
    rows = session.exec(
        select(Hero, Player)
        .join(Player, Hero.owner_id == Player.id)
        .order_by(col(Hero.victoire).desc(), col(Hero.or_).desc(), col(Hero.id))
        .limit(limit)
    ).all()
    return [
        LeaderboardEntry(
            rang=rang, nom=hero.nom, classe=hero.classe, or_=hero.or_,
            victoire=hero.victoire, joueur=player.username,
        )
        for rang, (hero, player) in enumerate(rows, start=1)
    ]
