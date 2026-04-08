import pytest


def test_validate_identifier_valid():
    from starburst_client import StarburstClient
    StarburstClient.validate_identifier("my_catalog")
    StarburstClient.validate_identifier("mcp2ohio")
    StarburstClient.validate_identifier("test_writes")
    StarburstClient.validate_identifier("table123")


def test_validate_identifier_rejects_injection():
    from starburst_client import StarburstClient
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("table; DROP TABLE x")
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("table'--")
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("")


def test_validate_identifier_rejects_reserved():
    from starburst_client import StarburstClient
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("SELECT")
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("drop")


def test_format_qualified_name():
    from starburst_client import StarburstClient
    assert StarburstClient.qualified_name("cat", "sch", "tbl") == '"cat"."sch"."tbl"'
    assert StarburstClient.qualified_name("cat", "sch") == '"cat"."sch"'


def test_client_init_basic_auth(monkeypatch):
    from starburst_client import StarburstClient
    monkeypatch.delenv("STARBURST_CLIENT_ID", raising=False)
    monkeypatch.setenv("STARBURST_HOST", "test.host.io")
    monkeypatch.setenv("STARBURST_PORT", "443")
    monkeypatch.setenv("STARBURST_USER", "testuser")
    monkeypatch.setenv("STARBURST_PASSWORD", "testpass")
    monkeypatch.setenv("STARBURST_CATALOG", "testcat")
    monkeypatch.setenv("STARBURST_SCHEMA", "testsch")
    client = StarburstClient()
    assert client.host == "test.host.io"
    assert client.auth_mode == "basic"


def test_client_init_oauth(monkeypatch):
    from starburst_client import StarburstClient
    monkeypatch.setenv("STARBURST_CLIENT_ID", "my_client")
    monkeypatch.setenv("STARBURST_CLIENT_SECRET", "my_secret")
    monkeypatch.setenv("STARBURST_TOKEN_URL", "https://example.com/oauth2/token")
    monkeypatch.setenv("STARBURST_HOST", "test.host.io")
    monkeypatch.setenv("STARBURST_PORT", "443")
    monkeypatch.setenv("STARBURST_CATALOG", "testcat")
    monkeypatch.setenv("STARBURST_SCHEMA", "testsch")
    client = StarburstClient()
    assert client.auth_mode == "oauth"
