import asyncio
import os
import random
import string
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db


SERVER_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://orders_user:orders_pass@postgres:5432/postgres"
)

def get_random_string(length=8):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    1. Generates a random DB name.
    2. Connects to system DB and creates that random DB.
    3. Yields engine connected to the random DB.
    4. Drops the random DB at the end.
    """
    # 1. Connect to system DB (postgres)
    sys_engine = create_async_engine(SERVER_URL, isolation_level="AUTOCOMMIT")

    # 2. Generate a random DB name and ensure it doesn't exist
    test_db_name = f"test_db_{get_random_string()}"
    
    # Simple check loop (unlikely to collide, but safe)
    async with sys_engine.begin() as conn:
        while True:
            result = await conn.execute(text(
                f"SELECT 1 FROM pg_database WHERE datname = '{test_db_name}'"
            ))
            if not result.scalar():
                break
            test_db_name = f"test_db_{get_random_string()}"

        print(f"--- Creating temporary test database: {test_db_name} ---")
        await conn.execute(text(f"CREATE DATABASE {test_db_name}"))

    await sys_engine.dispose()

    # 3. Connect to the NEW Random Test DB
    test_db_url = SERVER_URL.replace("/postgres", f"/{test_db_name}")
    engine = create_async_engine(test_db_url, poolclass=NullPool, echo=False)

    # 4. Create Schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 5. Cleanup: Drop the specific random DB we created
    await engine.dispose()
    
    print(f"--- Dropping temporary test database: {test_db_name} ---")
    sys_engine = create_async_engine(SERVER_URL, isolation_level="AUTOCOMMIT")
    async with sys_engine.begin() as conn:
        # Terminate connections first just in case
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{test_db_name}'
            AND pid <> pg_backend_pid();
        """))
        await conn.execute(text(f"DROP DATABASE {test_db_name}"))
    await sys_engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    session = session_maker()

    yield session

    await session.close()
    if transaction.is_active:
        await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()