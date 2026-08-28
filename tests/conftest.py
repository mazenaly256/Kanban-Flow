import pytest
from sqlalchemy import event
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
                                                        # we have nested inner connection to prevent the .commit() code inside te endpoints from persisting data inside the DB

        session = AsyncSession(bind=connection, join_transaction_mode="create_savepoint")       # do not really commit and persist the changes in the database, just save the data temporarily till the outer transaction is rolled back
                                                                                                # makes any .commit() on the db_session ends the save point, and any new action on the session starts a new savepoint, so any .commit() actually ends the savepoint, not the outer transaction
        yield session


        await session.close()
        await outer_transaction.rollback()



@pytest_asyncio.fixture
async def client(db_session):

    async def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)


    async with AsyncClient(transport=transport, base_url="http://test") as async_client:    # Takes base_url as there is no real server like what uvicorn introduces,
                                                                                            # The client is in the same process as the application, so it calls it directly like an ordinary function. There is not any network involved
        yield async_client


    app.dependency_overrides.clear()    # just for cleanliness