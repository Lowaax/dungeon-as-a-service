from sqlmodel import Field, SQLModel


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nom: str
    classe: str
    force: int
    agilite: int
    intelligence: int
    pv: int  # le héros est mort lorsque pv vaut 0
    pv_max: int
    salle_actuelle: str  # identifiant d'une salle de la carte
    or_: int = 0
    monstre_pv: int | None = None  # None : aucun combat en cours
    victoire: bool = False  # vrai lorsque la Liche est vaincue
    owner_id: int = Field(foreign_key="player.id", index=True)
