import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import uuid
from unittest.mock import patch, AsyncMock

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

TEST_USER_ID = str(uuid.uuid4())


@pytest.fixture
def mock_auth():
    """Override AuthKit dependency to return a fixed test user ID."""
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID
    yield TEST_USER_ID
    # get_db override is cleared in client fixture
    # but we need to clean this one too
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False)
    TestSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False)
    TestSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()