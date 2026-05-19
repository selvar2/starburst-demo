import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import app_jwt  # noqa: E402


def test_build_insert_verification_sql_with_explicit_columns():
    sql = "INSERT INTO mcp2ohio.test_writes.demo (id, name, amount) VALUES (1, 'alice', 10.0)"
    target = {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}

    verification_sql, reason = app_jwt._build_write_verification_sql(sql, "INSERT", target)

    assert reason is None
    assert verification_sql == (
        "SELECT * FROM mcp2ohio.test_writes.demo "
        "WHERE (id = 1 AND name = 'alice' AND amount = 10.0) LIMIT 100"
    )


def test_build_insert_verification_sql_without_columns_uses_describe(monkeypatch):
    class FakeClient:
        def execute(self, sql: str):
            assert sql == "DESCRIBE mcp2ohio.test_writes.demo"
            return {"rows": [["id"], ["name"], ["amount"]]}

    monkeypatch.setattr(app_jwt, "client", FakeClient())
    sql = "INSERT INTO mcp2ohio.test_writes.demo VALUES (1, 'alice', 10.0)"
    target = {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}

    verification_sql, reason = app_jwt._build_write_verification_sql(sql, "INSERT", target)

    assert reason is None
    assert verification_sql == (
        "SELECT * FROM mcp2ohio.test_writes.demo "
        "WHERE (id = 1 AND name = 'alice' AND amount = 10.0) LIMIT 100"
    )


def test_build_update_verification_sql_replaces_updated_where_value():
    sql = "UPDATE mcp2ohio.test_writes.demo SET name = 'new_name', amount = 11.5 WHERE id = 1 AND name = 'old_name'"
    target = {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}

    verification_sql, reason = app_jwt._build_write_verification_sql(sql, "UPDATE", target)

    assert reason is None
    assert verification_sql == (
        "SELECT * FROM mcp2ohio.test_writes.demo "
        "WHERE id = 1 AND name = 'new_name' AND amount = 11.5 LIMIT 100"
    )


def test_chat_insert_returns_verified_rows(monkeypatch):
    executed = []
    insert_sql = "INSERT INTO mcp2ohio.test_writes.demo (id, name, amount) VALUES (1, 'alice', 10.0)"
    verify_sql = (
        "SELECT * FROM mcp2ohio.test_writes.demo "
        "WHERE (id = 1 AND name = 'alice' AND amount = 10.0) LIMIT 100"
    )

    class FakeClient:
        catalog = "mcp2ohio"
        schema = "test_writes"
        host = "example"
        auth_mode = "jwt"

        def execute(self, sql: str):
            executed.append(sql)
            if sql == insert_sql:
                return {"rows_affected": 1, "status": "ok"}
            if sql == verify_sql:
                return {"columns": ["id", "name", "amount"], "rows": [[1, "alice", 10.0]]}
            raise AssertionError(sql)

    class StubNL2SQLService:
        def translate(self, message, catalog, schema, schema_cache):
            return SimpleNamespace(
                sql=message,
                source="sql",
                query_type="direct_sql",
                chart="table",
                matched_terms=[],
                grounding_reason=None,
                confidence=1.0,
                assumptions=[],
                followups=[],
                warnings=[],
                error=None,
            )

    monkeypatch.setattr(app_jwt, "client", FakeClient())
    monkeypatch.setattr(app_jwt, "_nl2sql_service", StubNL2SQLService())
    monkeypatch.setattr(app_jwt, "_check_permission", lambda perm_key: None)
    monkeypatch.setattr(app_jwt, "_enforce_destructive_confirm", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_jwt, "_suggest_chart", lambda columns, rows: "table")
    monkeypatch.setattr(app_jwt, "_final_chart_suggestion", lambda requested, suggested: suggested)

    payload = asyncio.run(app_jwt.chat(app_jwt.ChatRequest(
        message=insert_sql,
        context={"catalog": "mcp2ohio", "schema": "test_writes"},
    )))

    assert executed == [insert_sql, verify_sql]
    assert payload["sql"] == insert_sql
    assert payload["verification_sql"] == verify_sql
    assert payload["rows_affected"] == 1
    assert payload["columns"] == ["id", "name", "amount"]
    assert payload["rows"] == [[1, "alice", 10.0]]
    assert payload["row_count"] == 1
