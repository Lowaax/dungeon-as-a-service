"""Règles de combat des héros : POO pure, sans FastAPI ni base de données."""

import random
from abc import ABC, abstractmethod


class Heros(ABC):
    """Héros abstrait : chaque classe définit sa propre façon de frapper."""

    def __init__(self, force: int, agilite: int, intelligence: int) -> None:
        self.force = force
        self.agilite = agilite
        self.intelligence = intelligence

    @property
    def pv_max(self) -> int:
        return 20 + self.force * 2

    @abstractmethod
    def calculer_degats(self) -> tuple[int, bool]:
        """Renvoie (dégâts infligés, coup critique ?)."""

    def subir_degats(self, attaque_monstre: int) -> int:
        """Renvoie les dégâts réellement subis. Par défaut : l'attaque du monstre."""
        return attaque_monstre


class Guerrier(Heros):
    def calculer_degats(self) -> tuple[int, bool]:
        return 2 + self.force * 2, False

    def subir_degats(self, attaque_monstre: int) -> int:
        # Armure : un point de dégât absorbé, mais on subit toujours au moins 1
        return max(1, attaque_monstre - 1)


class Mage(Heros):
    def calculer_degats(self) -> tuple[int, bool]:
        return 1 + self.intelligence * 3, False


class Voleur(Heros):
    CHANCE_CRITIQUE = 1 / 3

    def __init__(
        self,
        force: int,
        agilite: int,
        intelligence: int,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(force, agilite, intelligence)
        # Générateur injectable pour rendre les tests déterministes
        self._rng = rng or random.Random()

    def calculer_degats(self) -> tuple[int, bool]:
        degats = 2 + self.agilite * 2
        critique = self._rng.random() < self.CHANCE_CRITIQUE
        return (degats * 2 if critique else degats), critique


# Associe le nom de classe stocké en base à la classe métier :
# le service n'a ainsi aucune condition sur la classe du héros.
CLASSES_HEROS: dict[str, type[Heros]] = {
    "guerrier": Guerrier,
    "mage": Mage,
    "voleur": Voleur,
}


def creer_heros(classe: str, force: int, agilite: int, intelligence: int) -> Heros:
    """Construit l'objet métier correspondant à la classe du héros."""
    return CLASSES_HEROS[classe](force, agilite, intelligence)
