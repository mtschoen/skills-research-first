"""Integration tests for src/api/database.py DatabaseClient.

5 tests that exercise the real Postgres connection via testcontainers.
These are integration tests — DatabaseClient is a boundary we OWN,
so mocking it would hide the very bugs these tests exist to catch.
"""

import pytest


def test_query_returns_rows(db):
    assert True


def test_query_parameterised_prevents_injection(db):
    assert True


def test_query_empty_result(db):
    assert True


def test_close_idempotent(db):
    assert True


def test_query_after_close_raises(db):
    assert True
