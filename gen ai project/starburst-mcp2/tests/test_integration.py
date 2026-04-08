"""Integration tests against live mcp2ohio catalog on free-cluster.

These tests create a temporary schema, run CRUD operations, and clean up.
Requires .env with valid Starburst credentials.
Skip with: pytest -m "not integration"
"""

import os
import sys
import pytest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from starburst_client import StarburstClient


pytestmark = pytest.mark.integration

TEST_CATALOG = "mcp2ohio"
TEST_SCHEMA = f"inttest_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def client():
    return StarburstClient()


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown(client):
    """Create test schema before tests, drop after."""
    client.execute(f'CREATE SCHEMA "{TEST_CATALOG}"."{TEST_SCHEMA}"')
    yield
    try:
        client.execute(f'DROP TABLE IF EXISTS "{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"')
    except Exception:
        pass
    try:
        client.execute(f'DROP SCHEMA "{TEST_CATALOG}"."{TEST_SCHEMA}"')
    except Exception:
        pass


def test_create_table(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    client.execute(f"CREATE TABLE {fqn} (id INTEGER, name VARCHAR, amount DOUBLE)")
    result = client.execute(f"DESCRIBE {fqn}")
    col_names = [row[0] for row in result["rows"]]
    assert "id" in col_names
    assert "name" in col_names
    assert "amount" in col_names


def test_insert(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    result = client.execute(f"INSERT INTO {fqn} VALUES (1, 'Alice', 100.0), (2, 'Bob', 200.0)")
    assert result["rows_affected"] == 2


def test_select(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    result = client.execute(f"SELECT * FROM {fqn} ORDER BY id")
    assert len(result["rows"]) == 2
    assert result["rows"][0][1] == "Alice"
    assert result["rows"][1][1] == "Bob"


def test_update(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    result = client.execute(f"UPDATE {fqn} SET amount = 150.0 WHERE id = 1")
    assert result["rows_affected"] == 1
    check = client.execute(f"SELECT amount FROM {fqn} WHERE id = 1")
    assert check["rows"][0][0] == 150.0


def test_delete(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    result = client.execute(f"DELETE FROM {fqn} WHERE id = 2")
    assert result["rows_affected"] == 1
    check = client.execute(f"SELECT * FROM {fqn}")
    assert len(check["rows"]) == 1


def test_truncate(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    client.execute(f"INSERT INTO {fqn} VALUES (3, 'Carol', 300.0)")
    client.execute(f"TRUNCATE TABLE {fqn}")
    result = client.execute(f"SELECT count(*) FROM {fqn}")
    assert result["rows"][0][0] == 0
