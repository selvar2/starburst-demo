"""Provider-agnostic LLM access for StarQuery AI."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Protocol


class ProviderError(RuntimeError):
    """Raised when an LLM provider cannot complete a request."""


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str = ""
    base_url: str = ""
    timeout_seconds: int = 30
    max_retries: int = 2


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    provider: str
    model: str


class LLMProvider(Protocol):
    config: LLMConfig

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        ...


class MockLLMProvider:
    def __init__(self, content: str = '{"sql":"SELECT 1"}'):
        self.config = LLMConfig(provider="mock", model="mock")
        self._content = content

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        return LLMResponse(content=self._content, provider="mock", model="mock")


class OpenAICompatibleProvider:
    """Chat-completions adapter used by OpenAI and OpenAI-compatible APIs."""

    def __init__(self, config: LLMConfig):
        self.config = config

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        url = self.config.base_url or _default_openai_compatible_url(self.config.provider)
        payload = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        data = _post_json_with_retries(url, payload, self.config)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Unexpected {self.config.provider} response shape") from exc
        return LLMResponse(content=content, provider=self.config.provider, model=self.config.model)


class AnthropicProvider:
    def __init__(self, config: LLMConfig):
        self.config = config

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        user_messages = [
            {"role": "assistant" if m.role == "assistant" else "user", "content": m.content}
            for m in messages
            if m.role != "system"
        ]
        payload = {
            "model": self.config.model,
            "max_tokens": 2048,
            "temperature": 0.1,
            "system": system,
            "messages": user_messages,
        }
        url = self.config.base_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        data = _post_json_with_retries(url, payload, self.config, headers=headers)
        try:
            content = "".join(part.get("text", "") for part in data.get("content", []))
        except AttributeError as exc:
            raise ProviderError("Unexpected anthropic response shape") from exc
        return LLMResponse(content=content, provider=self.config.provider, model=self.config.model)


def _post_json_with_retries(
    url: str,
    payload: dict,
    config: LLMConfig,
    headers: dict | None = None,
) -> dict:
    try:
        import requests
    except ImportError as exc:
        raise ProviderError("requests is required for live LLM provider calls") from exc

    request_headers = headers or {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    last_exc: Exception | None = None
    for attempt in range(config.max_retries + 1):
        try:
            response = requests.post(
                url,
                headers=request_headers,
                json=payload,
                timeout=config.timeout_seconds,
            )
            if response.status_code >= 400:
                raise ProviderError(f"{config.provider} returned HTTP {response.status_code}: {response.text[:300]}")
            return response.json()
        except (requests.RequestException, json.JSONDecodeError, ProviderError) as exc:
            last_exc = exc
            if attempt >= config.max_retries:
                break
            time.sleep(0.25 * (attempt + 1))
    raise ProviderError(str(last_exc))


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def build_provider_from_env() -> LLMProvider | None:
    enabled = os.getenv("LLM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return None

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider == "mock":
        return MockLLMProvider(os.getenv("LLM_MOCK_RESPONSE", '{"sql":"SELECT 1"}'))

    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("LLM_MODEL", "").strip()
    if not model:
        model = {
            "openai": "gpt-4.1-mini",
            "kimi": "kimi-k2.6",
            "deepseek": "deepseek-chat",
            "anthropic": "claude-3-5-sonnet-latest",
        }.get(provider, "gpt-4.1-mini")

    config = LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "").strip(),
        timeout_seconds=_env_int("LLM_TIMEOUT_SECONDS", 30),
        max_retries=_env_int("LLM_MAX_RETRIES", 2),
    )

    if provider in {"openai", "kimi", "deepseek"}:
        return OpenAICompatibleProvider(config)
    if provider in {"anthropic", "claude"}:
        object.__setattr__(config, "provider", "anthropic")
        return AnthropicProvider(config)
    raise ProviderError(f"Unsupported LLM_PROVIDER: {provider}")


def _default_openai_compatible_url(provider: str) -> str:
    if provider == "deepseek":
        return "https://api.deepseek.com/chat/completions"
    return "https://api.openai.com/v1/chat/completions"
