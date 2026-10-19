from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.database import get_session
from app.schemas.auth import PlayerCreate, PlayerRead, Token
from app.schemas.errors import ErrorResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post(
    "/register",
    response_model=PlayerRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse, "description": "USERNAME_TAKEN"}},
)
def register(data: PlayerCreate, session: Session = Depends(get_session)):
    """Crée un compte joueur (mot de passe haché)."""
    player = auth_service.register(session, data)
    return PlayerRead(id=player.id, username=player.username)


@router.post(
    "/login",
    response_model=Token,
    responses={401: {"model": ErrorResponse, "description": "INVALID_CREDENTIALS"}},
)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """Connexion (formulaire OAuth2, compatible bouton Authorize) : renvoie un token JWT."""
    player = auth_service.authenticate(session, form.username, form.password)
    return Token(access_token=auth_service.create_access_token(player))
