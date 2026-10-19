from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database import get_session
from app.models.player import Player
from app.schemas.errors import ErrorResponse
from app.schemas.hero import AttackResult, HeroCreate, HeroRead, MoveRequest, RoomRead
from app.services import hero_service
from app.services.auth_service import get_current_player

router = APIRouter(
    prefix="/heroes",
    tags=["Héros"],
    responses={401: {"model": ErrorResponse, "description": "Token absent ou invalide"}},
)

HERO_ERRORS = {
    403: {"model": ErrorResponse, "description": "NOT_YOUR_HERO"},
    404: {"model": ErrorResponse, "description": "HERO_NOT_FOUND"},
}
ACTION_ERRORS = {**HERO_ERRORS, 409: {"model": ErrorResponse, "description": "IN_COMBAT, NO_MONSTER ou HERO_DEAD"}}


@router.post("", response_model=HeroRead, status_code=status.HTTP_201_CREATED)
def create_hero(
    data: HeroCreate,
    session: Session = Depends(get_session),
    player: Player = Depends(get_current_player),
):
    """Crée un héros dans la salle de départ, PV au maximum."""
    return HeroRead.from_model(hero_service.create_hero(session, data, player))


@router.get("", response_model=list[HeroRead])
def list_heroes(session: Session = Depends(get_session), player: Player = Depends(get_current_player)):
    """Liste les héros du joueur connecté."""
    return [HeroRead.from_model(h) for h in hero_service.list_heroes(session, player)]


@router.get("/{hero_id}", response_model=HeroRead, responses=HERO_ERRORS)
def get_hero(hero_id: int, session: Session = Depends(get_session), player: Player = Depends(get_current_player)):
    """Consulte un héros (même mort)."""
    return HeroRead.from_model(hero_service.get_hero(session, hero_id, player))


@router.get("/{hero_id}/room", response_model=RoomRead, responses=HERO_ERRORS)
def get_room(hero_id: int, session: Session = Depends(get_session), player: Player = Depends(get_current_player)):
    """Décrit la salle où se trouve le héros."""
    return hero_service.describe_room(hero_service.get_hero(session, hero_id, player))


@router.post(
    "/{hero_id}/move",
    response_model=RoomRead,
    responses={**ACTION_ERRORS, 400: {"model": ErrorResponse, "description": "NO_EXIT"}},
)
def move(
    hero_id: int,
    body: MoveRequest,
    session: Session = Depends(get_session),
    player: Player = Depends(get_current_player),
):
    """Déplace le héros et renvoie la nouvelle salle. Entrer dans une salle hantée démarre un combat."""
    hero = hero_service.get_hero(session, hero_id, player)
    return hero_service.move(session, hero, body.direction.value)


@router.post("/{hero_id}/attack", response_model=AttackResult, responses=ACTION_ERRORS)
def attack(hero_id: int, session: Session = Depends(get_session), player: Player = Depends(get_current_player)):
    """Déroule un tour de combat : le héros frappe, puis le monstre riposte s'il survit."""
    hero = hero_service.get_hero(session, hero_id, player)
    return hero_service.attack(session, hero)


@router.post("/{hero_id}/rest", response_model=HeroRead, responses=ACTION_ERRORS)
async def rest(
    hero_id: int,
    session: Session = Depends(get_session),
    player: Player = Depends(get_current_player),
):
    """Repos de 3 secondes (non bloquant), puis PV restaurés au maximum."""
    hero = hero_service.get_hero(session, hero_id, player)
    return HeroRead.from_model(await hero_service.rest(session, hero))
