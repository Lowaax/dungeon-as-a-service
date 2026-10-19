# Dungeon as a Service — starter

Squelette fourni pour le projet bonus du module Python Backend & FastAPI.

## Installation (à faire une seule fois)

Prérequis : Python 3.10 ou plus récent (`python --version`).

```bash
# 1. Créer et activer un environnement virtuel
python -m venv .venv
# Windows (PowerShell) :
.venv\Scripts\Activate.ps1
# macOS / Linux :
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt
```

## Lancer l'API

Depuis la racine du projet (le dossier qui contient `app/`) :

```bash
fastapi dev app/main.py
```

Ouvrez ensuite http://127.0.0.1:8000/docs : la route `GET /health` doit répondre
`{"status": "ok", ...}`. Si c'est le cas, vous êtes prêts.

## Structure

```
app/
  main.py              point d'entrée, branchement des routers
  database.py          connexion SQLite (FOURNI)
  models/              tables SQLModel
  schemas/             schémas Pydantic d'entrée et de sortie
  domain/              classes métier (Heros, Guerrier, Mage, Voleur)
  services/            logique du jeu
    dungeon_map.py     lecture de la carte (FOURNI)
  routes/              routers FastAPI
data/dungeon_map.json  carte du donjon (FOURNI, ne pas modifier)
client/play.py         client terminal (BONUS)
```

## Réinitialiser la partie

Arrêtez le serveur et supprimez le fichier `dungeon.db` : il sera recréé au prochain lancement.
À faire aussi si vous ajoutez une colonne à une table (SQLite ne met pas à jour une table existante).

---

<!-- À COMPLÉTER PAR LE GROUPE AVANT LE RENDU -->

## Notre rendu

- **Membres du groupe :** _à compléter_
- **Lien du dépôt Git :** _à compléter_
- **Palier atteint :** 4
- **Bonus réalisés :**
  - B-1 client terminal : `client/play.py` (register, login, create, heroes, look, move, attack, rest, leaderboard ; token dans `.token`)
  - B-2 classement : `GET /leaderboard` (public, top 10 : vainqueurs d'abord, puis or)
  - B-3 tests : `pytest` (18 tests, base SQLite en mémoire : 201, 422, 400, 401, 403, 404, 409 et règles du domaine)
  - B-4 PostgreSQL : `docker-compose.yml` + variable `DATABASE_URL` (driver `psycopg` ajouté aux dépendances)
  - B-5 journalisation : logger `dungeon` (création, déplacements, tours de combat, repos, victoire)
- **Ce qui ne fonctionne pas / difficultés :**
  - Le bonus PostgreSQL n'a pas pu être testé en conditions réelles (Docker non démarré sur le poste) ; le code n'a pas besoin d'être modifié, seul `DATABASE_URL` change.
  - Le coup critique du voleur est aléatoire (probabilité 1/3 à chaque coup), pas strictement « un coup sur trois ».

### Choix techniques

- **Architecture** : `routes/` (HTTP uniquement) → `services/` (logique, base, carte) → `domain/` (règles de combat en POO pure).
- **Domaine** : `Heros` (ABC) avec `pv_max`, `calculer_degats()` abstraite et `subir_degats()` ; `Guerrier` (armure), `Mage`, `Voleur` (critique). Le dictionnaire `CLASSES_HEROS` associe la classe stockée à la classe métier : aucune condition sur la classe dans le service.
- **Validation** : `HeroCreate` (Pydantic) — longueur du nom, `Enum` pour la classe, stats `1..8`, somme = 10 via `model_validator`.
- **Sorties** : `HeroRead` n'expose ni `monstre_pv` ni `owner_id`, mais `en_combat` et `est_vivant`.
- **Erreurs métier** : toujours `{"detail": {"error": CODE, "message": ...}}` (`app/services/errors.py`). Codes : `HERO_NOT_FOUND`, `NOT_YOUR_HERO`, `NO_EXIT`, `IN_COMBAT`, `NO_MONSTER`, `HERO_DEAD`, `USERNAME_TAKEN`, `INVALID_CREDENTIALS`, `NOT_AUTHENTICATED`, `INVALID_TOKEN`.
- **Repos** : route `async def` avec `await asyncio.sleep(3)` : le serveur répond aux autres requêtes pendant le repos.
- **Sécurité** : mots de passe hachés (pwdlib / argon2), JWT HS256 signé avec `SECRET_KEY` (variable d'environnement, valeur par défaut pour le dev), login via `OAuth2PasswordRequestForm` (bouton Authorize de Swagger).

### Lancer les tests

```bash
python -m pytest -q
```
