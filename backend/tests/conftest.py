"""Pytest fixtures for Field Service smoke tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import get_db
from app.main import app


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - environment gate
        pytest.skip(f"Database unavailable for smoke tests: {exc}")
    return engine


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture
def client(db_session_factory):
    def _override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def dispatcher_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "dispatcher@demo.local", "password": "demo"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def tech_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "tech@demo.local", "password": "demo"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def other_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "other@demo.local", "password": "demo"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]
