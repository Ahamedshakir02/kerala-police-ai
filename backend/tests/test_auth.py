"""Backend Tests — Auth endpoints"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Use in-memory SQLite for testing
TEST_DB_URL = "sqlite+aiosqlite:///./test_kpai.db"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def test_db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    from app.core.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
async def client(test_db):
    from main import app
    from app.core.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    session_factory = async_sessionmaker(test_db, expire_on_commit=False)

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.anyio
async def test_seed_demo(client):
    resp = await client.post("/api/auth/seed-demo")
    assert resp.status_code == 201
    assert "KP001" in resp.json()["message"] or "already exist" in resp.json()["message"]


@pytest.mark.anyio
async def test_login_success(client):
    # Seed first
    await client.post("/api/auth/seed-demo")
    resp = await client.post("/api/auth/login", json={"badge_number": "KP001", "password": "test1234"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["officer"]["badge_number"] == "KP001"


@pytest.mark.anyio
async def test_login_invalid_password(client):
    resp = await client.post("/api/auth/login", json={"badge_number": "KP001", "password": "wrongpass"})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_unknown_officer(client):
    resp = await client.post("/api/auth/login", json={"badge_number": "KP999", "password": "test1234"})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_me(client):
    await client.post("/api/auth/seed-demo")
    login_resp = await client.post("/api/auth/login", json={"badge_number": "KP001", "password": "test1234"})
    token = login_resp.json()["access_token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["badge_number"] == "KP001"
