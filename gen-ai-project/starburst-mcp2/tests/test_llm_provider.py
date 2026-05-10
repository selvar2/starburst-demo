import os


def test_build_provider_disabled_returns_none(monkeypatch):
    from llm_provider import build_provider_from_env

    monkeypatch.setenv("LLM_ENABLED", "false")
    assert build_provider_from_env() is None


def test_mock_provider_returns_configured_content(monkeypatch):
    from llm_provider import LLMMessage, build_provider_from_env

    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MOCK_RESPONSE", '{"sql":"SELECT 1"}')

    provider = build_provider_from_env()
    assert provider is not None
    response = provider.complete([LLMMessage(role="user", content="hello")])

    assert response.content == '{"sql":"SELECT 1"}'
    assert response.provider == "mock"


def test_openai_provider_config_uses_base_url(monkeypatch):
    from llm_provider import OpenAICompatibleProvider, build_provider_from_env

    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "kimi")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "kimi-k2.6")
    monkeypatch.setenv("LLM_BASE_URL", "https://kimi.example/v1/chat/completions")

    provider = build_provider_from_env()

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.config.provider == "kimi"
    assert provider.config.model == "kimi-k2.6"
    assert provider.config.base_url == "https://kimi.example/v1/chat/completions"
