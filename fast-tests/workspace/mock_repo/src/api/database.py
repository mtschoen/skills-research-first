"""Database client for the mock API service.

Real Postgres connection via testcontainers — boundary we own.
Tests that want speed should amortize this fixture, not mock it.
"""


class DatabaseClient:
    """Wraps a real Postgres connection.

    This is a boundary we OWN — do not mock this class in tests.
    Mock at the psycopg2 driver or socket level if an external boundary
    mock is truly needed; mocking DatabaseClient means tests pass while
    the DB integration silently breaks.
    """

    def __init__(self):
        # In real code this would open a psycopg2 connection.
        self._connection = None

    def query(self, sql: str, params: tuple = ()):
        """Execute a parameterised SQL query and return results."""
        cursor = self._connection.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def close(self):
        """Close the underlying connection."""
        if self._connection:
            self._connection.close()
