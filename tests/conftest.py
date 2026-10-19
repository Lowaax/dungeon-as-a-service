import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.services import hero_service


@pytest.fixture
def client(monkeypatch):
    # Base SQLite en mémoire, recréée pour chaque test (dungeon.db n'est pas touché)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    monkeypatch.setattr(hero_service, "REST_DURATION_SECONDS", 0)
    yield TestClient(app)
    app.dependency_overrides.clear()


def auth_headers(client: TestClient, username: str = "alice", password: str = "secret") -> dict:
    client.post("/auth/register", json={"username": username, "password": password})
    token = client.post("/auth/login", data={"username": username, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


GUERRIER = {"nom": "Aragorn", "classe": "guerrier", "force": 6, "agilite": 2, "intelligence": 2}
