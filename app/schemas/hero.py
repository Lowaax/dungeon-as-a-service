from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from app.models.hero import Hero


class ClasseHeros(str, Enum):
    guerrier = "guerrier"
    mage = "mage"
    voleur = "voleur"


Statistique = Annotated[int, Field(ge=1, le=8)]


class HeroCreate(BaseModel):
    nom: str = Field(min_length=3, max_length=20)
    classe: ClasseHeros
    force: Statistique
    agilite: Statistique
    intelligence: Statistique

    @model_validator(mode="after")
    def verifier_somme_stats(self) -> "HeroCreate":
        total = self.force + self.agilite + self.intelligence
        if total != 10:
            raise ValueError(f"La somme des statistiques doit valoir 10 (actuellement {total})")
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"nom": "Aragorn", "classe": "guerrier", "force": 6, "agilite": 2, "intelligence": 2}
            ]
        }
    }


class HeroRead(BaseModel):
    """Réponse publique : monstre_pv et owner_id sont remplacés par en_combat / est_vivant."""

    id: int
    nom: str
    classe: ClasseHeros
    force: int
    agilite: int
    intelligence: int
    pv: int
    pv_max: int
    salle_actuelle: str
    or_: int
    victoire: bool
    en_combat: bool
    est_vivant: bool

    @classmethod
    def from_model(cls, hero: Hero) -> "HeroRead":
        return cls(
            id=hero.id,
            nom=hero.nom,
            classe=hero.classe,
            force=hero.force,
            agilite=hero.agilite,
            intelligence=hero.intelligence,
            pv=hero.pv,
            pv_max=hero.pv_max,
            salle_actuelle=hero.salle_actuelle,
            or_=hero.or_,
            victoire=hero.victoire,
            en_combat=hero.monstre_pv is not None,
            est_vivant=hero.pv > 0,
        )


class Direction(str, Enum):
    nord = "nord"
    sud = "sud"
    est = "est"
    ouest = "ouest"


class MoveRequest(BaseModel):
    direction: Direction

    model_config = {"json_schema_extra": {"examples": [{"direction": "nord"}]}}


class MonsterRead(BaseModel):
    nom: str
    pv: int
    pv_max: int
    attaque: int


class RoomRead(BaseModel):
    id: str
    nom: str
    description: str
    sorties: dict[str, str]
    monstre: MonsterRead | None = None


class AttackResult(BaseModel):
    degats_infliges: int
    critique: bool
    degats_subis: int
    pv_heros: int
    pv_monstre: int
    issue: Literal["en_cours", "monstre_vaincu", "heros_mort"]
    or_gagne: int
    victoire: bool


class LeaderboardEntry(BaseModel):
    rang: int
    nom: str
    classe: ClasseHeros
    or_: int
    victoire: bool
    joueur: str
