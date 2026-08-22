import pytest
from testcontainers.community.postgres import PostgresContainer

from alembic import command
from alembic.config import Config

@pytest.fixture(scope="session")    # runs at the beginning of each testing session and reuse the same object for every test
def postgres_server_container():
    with PostgresContainer("postgres:16") as container:
        yield container



@pytest.fixture(scope="session")
def apply_migrations(postgres_server_container):
    connection_url = postgres_server_container.get_connection_url()     # this is how we can connect the application with the containerized db server

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", connection_url)

    command.upgrade(alembic_cfg, "head")