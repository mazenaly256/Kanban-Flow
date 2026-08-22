import pytest

from testcontainers.community.postgres import PostgresContainer

@pytest.fixture(scope="session")    # runs at the beginning of each testing session and reuse the same object for every test
def postgres_server_container():
    with PostgresContainer("postgres:16") as container:
        yield container
