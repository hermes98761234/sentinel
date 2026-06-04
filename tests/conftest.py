import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from api.core.db import Base, get_db
from api.services.auth import create_api_key
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_db):
    engine = create_async_engine(TEST_DB_URL)
    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncSession() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def valid_api_key(db_session):
    raw_key = await create_api_key(db_session, owner="test")
    app.dependency_overrides[get_db] = lambda: db_session
    return raw_key
