import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Reusable payloads ─────────────────────────────────────────────────────────

@pytest.fixture
def register_payload():
    return {
        "email": "test@example.com",
        "password": "test123",
        "business_name": "TestShop",
        "agent_name": "Bella"
    }


@pytest.fixture
def registered_user(client, register_payload):
    """Registers a user and returns the response JSON."""
    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_token(registered_user):
    """Returns the JWT token from a registered user."""
    return registered_user["token"]