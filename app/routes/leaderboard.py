from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.hero import LeaderboardEntry
from app.services import hero_service

router = APIRouter(prefix="/leaderboard", tags=["Classement"])


@router.get("", response_model=list[LeaderboardEntry])
def leaderboard(session: Session = Depends(get_session)):
    """Route publique : les 10 meilleurs héros (vainqueurs d'abord, puis par or)."""
    return hero_service.leaderboard(session)
