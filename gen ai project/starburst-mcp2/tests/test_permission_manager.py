import os
import pytest
import tempfile
import yaml

def write_yaml(path, data):
    with open(path, "w") as f:
        yaml.dump(data, f)

SAMPLE_CONFIG = {
    "defaults": {
        "read": True, "insert": True, "update": False, "delete": False,
        "create_schema": False, "create_table": False, "drop_table": False,
        "drop_schema": False, "truncate": False, "merge": False, "execute_raw": False,
    },
    "profiles": {
        "read_only": {"read": True},
        "analyst": {"insert": True, "update": True, "delete": True, "create_table": True},
        "admin": {
            "insert": True, "update": True, "delete": True,
            "create_schema": True, "create_table": True,
            "drop_table": True, "drop_schema": True,
            "truncate": True, "merge": True, "execute_raw": True,
        },
    },
    "developers": {
        "alice": {"profile": "admin"},
        "bob": {"profile": "read_only"},
        "carol": {"profile": "analyst", "overrides": {"drop_table": True}},
    },
}

@pytest.fixture
def perm_file(tmp_path):
    path = tmp_path / "permissions.yaml"
    write_yaml(str(path), SAMPLE_CONFIG)
    return str(path)

@pytest.fixture
def manager(perm_file):
    from permission_manager import PermissionManager
    return PermissionManager(perm_file)

def test_admin_has_all_permissions(manager):
    perms = manager.resolve("alice")
    assert perms["read"] is True
    assert perms["execute_raw"] is True
    assert perms["drop_schema"] is True

def test_read_only_denies_writes(manager):
    perms = manager.resolve("bob")
    assert perms["read"] is True
    assert perms["insert"] is False
    assert perms["delete"] is False
    assert perms["drop_table"] is False

def test_read_only_inherits_defaults(manager):
    perms = manager.resolve("bob")
    assert perms["read"] is True
    assert perms["update"] is False

def test_overrides_extend_profile(manager):
    perms = manager.resolve("carol")
    assert perms["insert"] is True
    assert perms["update"] is True
    assert perms["drop_table"] is True
    assert perms["drop_schema"] is False

def test_unknown_developer_gets_defaults(manager):
    perms = manager.resolve("unknown_user")
    assert perms["read"] is True
    assert perms["insert"] is True
    assert perms["update"] is False

def test_check_allowed(manager):
    assert manager.check("alice", "execute_raw") is True
    assert manager.check("bob", "delete") is False

def test_check_returns_error_message(manager):
    allowed, msg = manager.check_with_message("bob", "delete")
    assert allowed is False
    assert "not permitted" in msg
    assert "bob" in msg

def test_hot_reload(perm_file, manager):
    assert manager.check("bob", "delete") is False
    import time
    time.sleep(0.1)
    config = SAMPLE_CONFIG.copy()
    config["developers"] = {**config["developers"], "bob": {"profile": "admin"}}
    write_yaml(perm_file, config)
    assert manager.check("bob", "delete") is True
