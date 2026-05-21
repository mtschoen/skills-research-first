"""Pytest fixtures for the mock API service test suite.

The `db` fixture is function-scoped (the default), meaning it spins up a
fresh testcontainers Postgres for every test.  Per-test setup is ~3 seconds,
making the 30-test suite wall-clock ~90 seconds total.

matches scenario 1 — per-test setup ~3s.
To fix: change scope to 'session' (or 'module') and truncate tables between
tests rather than rebuilding the schema each time.
"""

import pytest


@pytest.fixture()  # function scope — deliberately expensive; scenario 1
def db():
    """Spin up a real Postgres via testcontainers and run migrations.

    Cost: ~3 seconds per test (container start + schema migration).
    Shared across all tests in this conftest via scope change would drop
    total wall-clock from ~90s to ~5s for the 30-test suite.
    """
    # In real code: container = PostgresContainer("postgres:15"); container.start()
    # run_migrations(container.get_connection_url())
    # yield DatabaseClient(container.get_connection_url())
    # container.stop()
    yield None  # stub — not runnable


@pytest.fixture()
def app(db):
    """Wire the full application with a real database backend."""
    # In real code: yield create_app(database=db)
    yield None  # stub
