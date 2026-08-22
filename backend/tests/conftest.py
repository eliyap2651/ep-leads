"""Shared pytest fixtures.

Tests run against a real PostgreSQL database (spec: "use a real Production
database", and dedup/scoring logic depends on real SQL behavior) - point
TEST_DATABASE_URL at a disposable Postgres instance (docker-compose's `postgres`
service works fine; docker-compose.test.yml spins up an isolated one on port 5433).
Run with: `docker compose -f docker-compose.yml -f docker-compose.test.yml up -d postgres`
then `pytest` from the backend/ directory.
"""

import asyncio
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault(
    "DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://ep_leads:ep_leads@localhost:5433/ep_leads_test")
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ANTHROPIC_API_KEY", "")

from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.database import get_db  # noqa: E402


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    session_factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User

    user = User(email="admin@test.local", hashed_password=hash_password("TestPass123!"), full_name="Test Admin", role=UserRole.ADMIN)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    resp = await client.post("/api/auth/login", json={"email": "admin@test.local", "password": "TestPass123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
