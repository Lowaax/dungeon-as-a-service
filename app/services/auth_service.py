"""Comptes joueurs : hachage des mots de passe (pwdlib) et tokens JWT (PyJWT)."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.database import get_session
from app.models.player import Player
from app.schemas.auth import PlayerCreate
from app.services.errors import game_error, unauthorized

# Clé lue depuis l'environnement ; la valeur par défaut ne sert qu'au développement
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-a-changer-en-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def register(session: Session, data: PlayerCreate) -> Player:
    existing = session.exec(select(Player).where(Player.username == data.username)).first()
    if existing:
        raise game_error(status.HTTP_409_CONFLICT, "USERNAME_TAKEN", "Ce nom d'utilisateur est déjà pris.")
    player = Player(username=data.username, hashed_password=password_hash.hash(data.password))
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


def authenticate(session: Session, username: str, password: str) -> Player:
    player = session.exec(select(Player).where(Player.username == username)).first()
    if player is None or not password_hash.verify(password, player.hashed_password):
        raise unauthorized("INVALID_CREDENTIALS", "Nom d'utilisateur ou mot de passe incorrect.")
    return player


def create_access_token(player: Player) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(player.id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_player(
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Player:
    """Dépendance : renvoie le joueur du token, ou lève une 401."""
    if token is None:
        raise unauthorized("NOT_AUTHENTICATED", "Authentification requise.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        player_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized("INVALID_TOKEN", "Token invalide ou expiré.")
    player = session.get(Player, player_id)
    if player is None:
        raise unauthorized("INVALID_TOKEN", "Token invalide ou expiré.")
    return player
