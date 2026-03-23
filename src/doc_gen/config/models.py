"""Pydantic configuration models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OPENAI_COMPATIBLE = "openai_compatible"  # For custom providers (moonshot, deepseek, etc.)


# Default API base URLs per provider
PROVIDER_BASE_URLS: dict[str, str] = {
    LLMProvider.OPENAI: "https://api.openai.com/v1",
    LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
    LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
}

# Default models per provider
PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    LLMProvider.OPENAI: "gpt-4o",
    LLMProvider.ANTHROPIC: "claude-sonnet-4-20250514",
    LLMProvider.OPENROUTER: "anthropic/claude-sonnet-4-20250514",
}


class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OPENAI
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    timeout: int = 120
    max_retries: int = 3
    temperature: float = 0.7

    def get_base_url(self) -> str:
        return self.base_url or PROVIDER_BASE_URLS.get(self.provider, "")

    def get_model(self) -> str:
        return self.model or PROVIDER_DEFAULT_MODELS.get(self.provider, "")

    def uses_openai_protocol(self) -> bool:
        """Whether this provider uses OpenAI-compatible chat/completions API."""
        return self.provider != LLMProvider.ANTHROPIC


class AppConfig(BaseModel):
    """Top-level application configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    data_dir: str = "~/.doc-gen/data"
    log_level: str = "INFO"
    default_granularity: str = "standard"
    default_doc_type: str = "tutorial"
    language: str = "en"
