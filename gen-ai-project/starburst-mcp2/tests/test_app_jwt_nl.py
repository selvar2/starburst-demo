"""Unit tests for the NL-driven DDL/DML extension in app_jwt.py.

These tests exercise the helper functions only (_nl_to_sql, _classify_sql,
_validate_fq, _enforce_destructive_confirm, _check_permission). They do not
hit the live Starburst cluster — `client.execute` is never called.
"""

import os
import sys
from pathlib import Path

import pytest

# Allow importing app_jwt as a top-level module.
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import app_jwt  # noqa: E402


# ---------------------------------------------------------------------------
# _classify_sql
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sql,expected", [
    ("SELECT * FROM x.y.z",                ("SELECT", "read")),
    ("  with q as (select 1) select * from q", ("WITH", "read")),
    ("SHOW TABLES FROM x.y",               ("SHOW", "read")),
    ("DESCRIBE x.y.z",                     ("DESCRIBE", "read")),
    ("INSERT INTO x.y.z VALUES (1)",       ("INSERT", "insert")),
    ("UPDATE x.y.z SET a=1",               ("UPDATE", "update")),
    ("DELETE FROM x.y.z WHERE a=1",        ("DELETE", "delete")),
    ("MERGE INTO x.y.z USING ...",         ("MERGE", "merge")),
    ("TRUNCATE TABLE x.y.z",               ("TRUNCATE", "truncate")),
    ("DROP TABLE x.y.z",                   ("DROP TABLE", "drop_table")),
    ("DROP SCHEMA x.y",                    ("DROP SCHEMA", "drop_schema")),
    ("CREATE SCHEMA x.y",                  ("CREATE SCHEMA", "create_schema")),
    ("CREATE TABLE x.y.z (a INT)",         ("CREATE TABLE", "create_table")),
    ("ALTER TABLE x.y.z ADD COLUMN b INT", ("ALTER", "execute_raw")),
])
def test_classify_sql(sql, expected):
    assert app_jwt._classify_sql(sql) == expected


# ---------------------------------------------------------------------------
# _validate_fq — happy paths
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sql,op,expected", [
    ("INSERT INTO mcp2ohio.test_writes.demo VALUES (1)", "INSERT",
        {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}),
    ("UPDATE mcp2ohio.test_writes.demo SET a=1", "UPDATE",
        {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}),
    ("DELETE FROM mcp2ohio.test_writes.demo WHERE id=1", "DELETE",
        {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}),
    ("TRUNCATE TABLE mcp2ohio.test_writes.demo", "TRUNCATE",
        {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}),
    ("DROP TABLE mcp2ohio.test_writes.demo", "DROP TABLE",
        {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}),
    ("CREATE SCHEMA mcp2ohio.new_sch", "CREATE SCHEMA",
        {"catalog": "mcp2ohio", "schema": "new_sch"}),
    ("DROP SCHEMA mcp2ohio.old_sch", "DROP SCHEMA",
        {"catalog": "mcp2ohio", "schema": "old_sch"}),
])
def test_validate_fq_accepts_fully_qualified(sql, op, expected):
    assert app_jwt._validate_fq(sql, op) == expected


# ---------------------------------------------------------------------------
# _validate_fq — rejection cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sql,op", [
    ("INSERT INTO demo VALUES (1)",               "INSERT"),       # 1 part
    ("INSERT INTO test_writes.demo VALUES (1)",   "INSERT"),       # 2 parts
    ("DELETE FROM demo WHERE id=1",               "DELETE"),
    ("UPDATE demo SET a=1",                       "UPDATE"),
    ("TRUNCATE TABLE demo",                       "TRUNCATE"),
    ("DROP TABLE demo",                           "DROP TABLE"),
    ("DROP SCHEMA my_sch",                        "DROP SCHEMA"),  # 1 part
    ("CREATE SCHEMA my_sch",                      "CREATE SCHEMA"),
    ("CREATE TABLE mcp2ohio.test_writes.demo.extra (a INT)", "CREATE TABLE"),  # 4 parts
])
def test_validate_fq_rejects_underqualified(sql, op):
    with pytest.raises(app_jwt.FQValidationError):
        app_jwt._validate_fq(sql, op)


def test_validate_fq_rejects_invalid_identifier():
    with pytest.raises(app_jwt.FQValidationError):
        app_jwt._validate_fq("DELETE FROM mcp2ohio.test_writes.123bad WHERE 1=1", "DELETE")


def test_validate_fq_skips_read_ops():
    # SELECT/SHOW/DESCRIBE are exempt — should return {}
    assert app_jwt._validate_fq("SELECT * FROM x", "SELECT") == {}
    assert app_jwt._validate_fq("SHOW TABLES",     "SHOW")   == {}


# ---------------------------------------------------------------------------
# _enforce_destructive_confirm
# ---------------------------------------------------------------------------

def test_destructive_requires_confirm():
    target = {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}
    with pytest.raises(app_jwt.ConfirmRequired):
        app_jwt._enforce_destructive_confirm("drop_table", "DROP TABLE", target, confirm=False)


def test_destructive_passes_with_confirm():
    target = {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}
    # No exception expected.
    app_jwt._enforce_destructive_confirm("drop_table", "DROP TABLE", target, confirm=True)


def test_nondestructive_does_not_require_confirm():
    target = {"catalog": "mcp2ohio", "schema": "test_writes", "table": "demo"}
    app_jwt._enforce_destructive_confirm("insert", "INSERT", target, confirm=False)
    app_jwt._enforce_destructive_confirm("update", "UPDATE", target, confirm=False)


# ---------------------------------------------------------------------------
# _check_permission
# ---------------------------------------------------------------------------

def test_perm_admin_allows_destructive(monkeypatch):
    # admin profile is wired in permissions.yaml for prakashrajr666.
    monkeypatch.setattr(app_jwt, "_developer", "prakashrajr666")
    app_jwt._check_permission("drop_table")  # no exception


def test_perm_intern_blocked_on_write(monkeypatch):
    monkeypatch.setattr(app_jwt, "_developer", "dev_intern")
    with pytest.raises(app_jwt.PermissionDenied):
        app_jwt._check_permission("insert")
    with pytest.raises(app_jwt.PermissionDenied):
        app_jwt._check_permission("drop_table")


def test_perm_unknown_developer_blocked(monkeypatch):
    monkeypatch.setattr(app_jwt, "_developer", "no_such_dev")
    with pytest.raises(app_jwt.PermissionDenied):
        app_jwt._check_permission("delete")


# ---------------------------------------------------------------------------
# _nl_to_sql — existing SELECT path still works
# ---------------------------------------------------------------------------

def test_nl_select_unchanged():
    sql = app_jwt._nl_to_sql("show all tables", "mcp2ohio", "test_writes")
    assert sql == "SHOW TABLES FROM mcp2ohio.test_writes"

    sql = app_jwt._nl_to_sql("describe demo", "mcp2ohio", "test_writes")
    assert sql == "DESCRIBE mcp2ohio.test_writes.demo"

    sql = app_jwt._nl_to_sql("count rows in demo", "mcp2ohio", "test_writes")
    assert sql == "SELECT COUNT(*) FROM mcp2ohio.test_writes.demo"


# ---------------------------------------------------------------------------
# _nl_to_sql — DML
# ---------------------------------------------------------------------------

def test_nl_delete_qualifies_bare_table():
    sql = app_jwt._nl_to_sql("delete from demo where id=1", "mcp2ohio", "test_writes")
    assert sql == "DELETE FROM mcp2ohio.test_writes.demo WHERE id=1"


def test_nl_delete_passes_dotted_form():
    sql = app_jwt._nl_to_sql(
        "delete from mcp2ohio.test_writes.demo where id=1",
        "mcp2ohio", "test_writes",
    )
    # The raw-SQL passthrough catches dotted forms before the NL pattern;
    # either way the resulting SQL is the same fully-qualified statement.
    assert sql.upper().startswith("DELETE FROM MCP2OHIO.TEST_WRITES.DEMO")


def test_nl_update():
    sql = app_jwt._nl_to_sql("update demo set name='x' where id=1", "mcp2ohio", "test_writes")
    assert sql == "UPDATE mcp2ohio.test_writes.demo SET name='x' WHERE id=1"


def test_nl_insert():
    sql = app_jwt._nl_to_sql("insert into demo values (1, 'a', 1.0)", "mcp2ohio", "test_writes")
    assert sql == "INSERT INTO mcp2ohio.test_writes.demo values (1, 'a', 1.0)"


# ---------------------------------------------------------------------------
# _nl_to_sql — DDL
# ---------------------------------------------------------------------------

def test_nl_truncate():
    sql = app_jwt._nl_to_sql("truncate demo", "mcp2ohio", "test_writes")
    assert sql == "TRUNCATE TABLE mcp2ohio.test_writes.demo"


def test_nl_drop_table():
    sql = app_jwt._nl_to_sql("drop table demo", "mcp2ohio", "test_writes")
    assert sql == "DROP TABLE mcp2ohio.test_writes.demo"


def test_nl_drop_schema_qualifies_bare():
    sql = app_jwt._nl_to_sql("drop schema scratch", "mcp2ohio", "test_writes")
    assert sql == "DROP SCHEMA mcp2ohio.scratch"


def test_nl_create_schema():
    sql = app_jwt._nl_to_sql("create schema scratch", "mcp2ohio", "test_writes")
    assert sql == "CREATE SCHEMA mcp2ohio.scratch"


# ---------------------------------------------------------------------------
# Context override — explicit hints route DDL/DML to a different schema
# ---------------------------------------------------------------------------

def test_nl_with_explicit_schema_hint():
    sql = app_jwt._nl_to_sql(
        "delete from demo where id=1, demo is part of test_writes schema and part of mcp2ohio catalog",
        "wrong_cat", "wrong_sch",
    )
    assert "mcp2ohio.test_writes.demo" in sql
    assert "wrong_cat" not in sql


# ---------------------------------------------------------------------------
# Business-user NL INSERT — happy paths
# ---------------------------------------------------------------------------

def test_nl_insert_verbose_form():
    sql = app_jwt._nl_to_sql(
        "Add a new row into catalog mcp2ohio, schema test_writes, table demo "
        "with id 777, name nl_test, and amount 7.7",
        "any", "any",
    )
    assert sql == (
        "INSERT INTO mcp2ohio.test_writes.demo (id, name, amount) "
        "VALUES (777, 'nl_test', 7.7)"
    )


def test_nl_insert_dotted_with_where():
    sql = app_jwt._nl_to_sql(
        "Insert a record into mcp2ohio.test_writes.demo "
        "where id = 888, name = cols_form, and amount = 1.5",
        "any", "any",
    )
    assert sql == (
        "INSERT INTO mcp2ohio.test_writes.demo (id, name, amount) "
        "VALUES (888, 'cols_form', 1.5)"
    )


def test_nl_insert_split_target():
    sql = app_jwt._nl_to_sql(
        "In catalog mcp2ohio, schema test_writes, add a row to table demo "
        "with id 901, name fq_form, and amount 9.99",
        "any", "any",
    )
    assert sql == (
        "INSERT INTO mcp2ohio.test_writes.demo (id, name, amount) "
        "VALUES (901, 'fq_form', 9.99)"
    )


def test_nl_insert_quoted_value_preserves_string():
    sql = app_jwt._nl_to_sql(
        "Add a row into catalog mcp2ohio, schema test_writes, table demo "
        "with id 5, name 'John Doe', amount 100",
        "any", "any",
    )
    assert "VALUES (5, 'John Doe', 100)" in sql


def test_nl_insert_null_and_bool_literals():
    sql = app_jwt._nl_to_sql(
        "Add a record into catalog c, schema s, table t with a 1, b null, c true",
        "any", "any",
    )
    assert sql == "INSERT INTO c.s.t (a, b, c) VALUES (1, NULL, TRUE)"


# ---------------------------------------------------------------------------
# Business-user NL INSERT — rejection cases (no guessing!)
# ---------------------------------------------------------------------------

def test_nl_insert_missing_catalog_rejected():
    with pytest.raises(app_jwt.FQValidationError) as ei:
        app_jwt._nl_to_sql(
            "Add a new row into schema test_writes, table demo with id 1, name a",
            "any", "any",
        )
    assert "catalog" in str(ei.value).lower()


def test_nl_insert_missing_table_rejected():
    with pytest.raises(app_jwt.FQValidationError) as ei:
        app_jwt._nl_to_sql(
            "Add a new row into catalog mcp2ohio, schema test_writes with id 1",
            "any", "any",
        )
    assert "table" in str(ei.value).lower()


def test_nl_insert_missing_values_rejected():
    with pytest.raises(app_jwt.FQValidationError):
        app_jwt._nl_to_sql(
            "Add a new row into catalog c, schema s, table t",
            "any", "any",
        )


def test_nl_insert_reserved_word_column_rejected():
    with pytest.raises(app_jwt.FQValidationError):
        app_jwt._nl_to_sql(
            "Add a row into catalog c, schema s, table t with select 1",
            "any", "any",
        )


def test_nl_insert_does_not_intercept_dev_sql():
    # Existing developer-SQL forms must continue to work unchanged.
    sql = app_jwt._nl_to_sql(
        "INSERT INTO mcp2ohio.test_writes.demo VALUES (901, 'fq_form', 9.99)",
        "any", "any",
    )
    # The trigger requires "row" or "record" — raw "INSERT INTO" passes through
    # the existing flow (raw-SQL passthrough or simple insert pattern).
    assert sql.upper().startswith("INSERT INTO MCP2OHIO.TEST_WRITES.DEMO")
    assert "(901" in sql or "VALUES (901" in sql


# ---------------------------------------------------------------------------
# Business-user NL UPDATE — happy paths
# ---------------------------------------------------------------------------

def test_nl_update_verbose_in_catalog():
    sql = app_jwt._nl_to_sql(
        "In catalog mcp2ohio, schema test_writes, table demo, "
        "update the row where id = 2 and set name to updated_via_nl",
        "any", "any",
    )
    assert sql == (
        "UPDATE mcp2ohio.test_writes.demo "
        "SET name = 'updated_via_nl' WHERE id = 2"
    )


def test_nl_update_change_form():
    sql = app_jwt._nl_to_sql(
        "Change amount to 1500.5 in catalog mcp2ohio, schema test_writes, "
        "table demo for the row where name = 'hello'",
        "any", "any",
    )
    assert sql == (
        "UPDATE mcp2ohio.test_writes.demo "
        "SET amount = 1500.5 WHERE name = 'hello'"
    )


def test_nl_update_dotted_and_set():
    sql = app_jwt._nl_to_sql(
        "Update mcp2ohio.test_writes.demo and set amount = 999 where id = 888",
        "any", "any",
    )
    assert sql == (
        "UPDATE mcp2ohio.test_writes.demo SET amount = 999 WHERE id = 888"
    )


def test_nl_update_value_types():
    sql = app_jwt._nl_to_sql(
        "Update c.s.t and set a = 1, b = null, c = true where id = 1",
        "any", "any",
    )
    # Single 'set' picks up the first pair only — for multi-column updates the
    # business form is "set X to Y and set Z to W". This test pins the
    # canonical single-column behavior with type rendering.
    assert sql.startswith("UPDATE c.s.t SET a = 1 ")
    assert "WHERE id = 1" in sql


def test_nl_update_multiple_set_pairs():
    sql = app_jwt._nl_to_sql(
        "Update c.s.t and set a = 1 and set b = 'x' where id = 1",
        "any", "any",
    )
    assert sql == "UPDATE c.s.t SET a = 1, b = 'x' WHERE id = 1"


# ---------------------------------------------------------------------------
# Business-user NL UPDATE — rejection cases
# ---------------------------------------------------------------------------

def test_nl_update_missing_where_rejected():
    with pytest.raises(app_jwt.FQValidationError) as ei:
        app_jwt._nl_to_sql(
            "Update mcp2ohio.test_writes.demo and set amount = 999",
            "any", "any",
        )
    assert "where" in str(ei.value).lower()


def test_nl_update_missing_schema_rejected():
    with pytest.raises(app_jwt.FQValidationError) as ei:
        app_jwt._nl_to_sql(
            "In catalog mcp2ohio, table demo, update the row where id=1 and set name to a",
            "any", "any",
        )
    assert "schema" in str(ei.value).lower()


def test_nl_update_missing_set_rejected():
    with pytest.raises(app_jwt.FQValidationError):
        app_jwt._nl_to_sql(
            "In catalog c, schema s, table t, update the row where id = 1",
            "any", "any",
        )


def test_nl_update_reserved_word_column_rejected():
    with pytest.raises(app_jwt.FQValidationError):
        app_jwt._nl_to_sql(
            "Update c.s.t and set select = 1 where id = 1",
            "any", "any",
        )


# Existing technical-user UPDATE forms (simple regex) must still work.
def test_nl_update_simple_dev_form_still_works():
    sql = app_jwt._nl_to_sql(
        "update demo set name='x' where id=1",
        "mcp2ohio", "test_writes",
    )
    assert sql == "UPDATE mcp2ohio.test_writes.demo SET name='x' WHERE id=1"


def test_nl_update_raw_sql_unchanged():
    sql = app_jwt._nl_to_sql(
        "UPDATE mcp2ohio.test_writes.demo SET amount=999 WHERE id=888",
        "any", "any",
    )
    assert sql.upper().startswith("UPDATE MCP2OHIO.TEST_WRITES.DEMO")
    assert "WHERE ID=888" in sql.upper()
