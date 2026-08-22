import pytest
from testcontainers.community.postgres import PostgresContainer

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from alembic import command
from alembic.config import Config

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db

@pytest.fixture(scope="session")    # runs at the beginning of each testing session and reuse the same object for every test
def postgres_server_container():
    with PostgresContainer("postgres:16") as container:
        yield container



@pytest.fixture(scope="session")
def apply_migrations(postgres_server_container):
    connection_url = postgres_server_container.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )   # this is how we can connect the application with the containerized db server
        # uses async driver instead of the sync one

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", connection_url)

    command.upgrade(alembic_cfg, "head")    # triggers Alembic's env.py file execution



@pytest_asyncio.fixture(scope="session")    # creates an engine (that creates and manages the connections with db, the connection pool) once per testing session
async def test_engine(postgres_server_container, apply_migrations):
    connection_url = postgres_server_container.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(connection_url)

    yield engine

    await engine.dispose()



@pytest_asyncio.fixture     # does real async DB work, and runs for every single testing function
async def db_session(test_engine):
    async with test_engine.connect() as connection:
        outer_transaction = await connection.begin()    # this is always rolled back to clear the changes that happened during the test

        session = AsyncSession(bind=connection, join_transaction_mode="create_savepoint")

        yield session

        await session.close()
        await outer_transaction.rollback()




@pytest_asyncio.fixture
async def client(db_session):

    async def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as async_client:    # takes base_url as there is no real server like what uvicorn introduces,
                                                                                            # the client is in the same process as the application, so it calls it directly like an ordinary function
                                                                                            # there is not any network involved
        yield async_client

    app.dependency_overrides.clear()    # just for cleanliness