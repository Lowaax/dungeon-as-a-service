"""Erreurs métier au format imposé : {"detail": {"error": ..., "message": ...}}."""

from fastapi import HTTPException, status


def game_error(status_code: int, error: str, message: str, headers: dict | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": error, "message": message},
        headers=headers,
    )


def hero_not_found(hero_id: int) -> HTTPException:
    return game_error(status.HTTP_404_NOT_FOUND, "HERO_NOT_FOUND", f"Aucun héros avec l'identifiant {hero_id}.")


def not_your_hero() -> HTTPException:
    return game_error(status.HTTP_403_FORBIDDEN, "NOT_YOUR_HERO", "Ce héros appartient à un autre joueur.")


def hero_dead() -> HTTPException:
    return game_error(status.HTTP_409_CONFLICT, "HERO_DEAD", "Votre héros est mort, il ne peut plus agir.")


def in_combat() -> HTTPException:
    return game_error(status.HTTP_409_CONFLICT, "IN_COMBAT", "Un monstre vous barre la route : combattez-le d'abord !")


def no_monster() -> HTTPException:
    return game_error(status.HTTP_409_CONFLICT, "NO_MONSTER", "Il n'y a aucun monstre à attaquer ici.")


def no_exit(direction: str) -> HTTPException:
    return game_error(status.HTTP_400_BAD_REQUEST, "NO_EXIT", f"Il n'y a pas de passage vers le {direction}.")


def unauthorized(error: str, message: str) -> HTTPException:
    return game_error(
        status.HTTP_401_UNAUTHORIZED, error, message, headers={"WWW-Authenticate": "Bearer"}
    )
