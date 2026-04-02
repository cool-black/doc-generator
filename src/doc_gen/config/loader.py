"""Configuration file loading and saving."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

import yaml

from doc_gen.config.models import AppConfig, LLMConfig, LLMProvider

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""

    pass

CONFIG_DIR = Path.home() / ".doc-gen"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# .env file search order: project root (cwd), then package root
_ENV_SEARCH_PATHS = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent.parent.parent.parent / ".env",
]


def _load_dotenv() -> Path | None:
    """Load .env file into os.environ (simple implementation, no dependency).

    Returns the path of the loaded .env file, or None if not found.
    """
    for env_path in _ENV_SEARCH_PATHS:
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if key and key not in os.environ:  # don't override existing env
                        os.environ[key] = value
            logger.debug("Loaded .env from %s", env_path)
            return env_path  # stop after first .env found

    # No .env file found - log helpful warning
    searched = ", ".join(str(p) for p in _ENV_SEARCH_PATHS)
    logger.warning("No .env file found. Searched: %s", searched)
    return None


def _substitute_env_vars(value: str) -> str:
    """Replace ${VAR} or $VAR patterns with environment variable values."""
    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, match.group(0))

    return re.sub(r"\$\{(\w+)\}|\$(\w+)", replacer, value)


def _process_env_vars(data: dict) -> dict:  # type: ignore[type-arg]
    """Recursively substitute environment variables in string values."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = _substitute_env_vars(value)
        elif isinstance(value, dict):
            result[key] = _process_env_vars(value)
        else:
            result[key] = value
    return result


def _config_from_env() -> AppConfig:
    """Build AppConfig from LLM_* environment variables."""
    provider_str = os.environ.get("LLM_PROVIDER", "openai").lower()
    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        # Unknown provider name (moonshot, deepseek, etc.) → treat as OpenAI-compatible
        provider = LLMProvider.OPENAI_COMPATIBLE

    llm = LLMConfig(
        provider=provider,
        api_key=os.environ.get("LLM_API_KEY", ""),
        model=os.environ.get("LLM_MODEL", ""),
        base_url=os.environ.get("LLM_BASE_URL", "").strip(),
        timeout=int(os.environ.get("LLM_TIMEOUT", "300")),
        temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
    )
    return AppConfig(llm=llm)


def load_config(require_api_key: bool = False) -> AppConfig:
    """Load configuration. Priority: .env > config.yaml > defaults.

    Args:
        require_api_key: If True, raise ConfigError when API key is not configured.

    Raises:
        ConfigError: If require_api_key is True and no API key is found.
    """
    _load_dotenv()

    # If LLM_API_KEY is set in env (from .env or system), use env-based config
    if os.environ.get("LLM_API_KEY"):
        return _config_from_env()

    # Fall back to YAML config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        data = _process_env_vars(raw)
        config = AppConfig.model_validate(data)
        if require_api_key and not config.llm.api_key:
            raise ConfigError(
                "API key not configured. Please set LLM_API_KEY in your .env file:\n"
                "  LLM_API_KEY=your-api-key-here\n\n"
                f"Expected .env file location: {_ENV_SEARCH_PATHS[0]}"
            )
        return config

    # No configuration found
    if require_api_key:
        raise ConfigError(
            "API key not configured. Please create a .env file with:\n"
            "  LLM_API_KEY=your-api-key-here\n"
            "  LLM_PROVIDER=openai\n"
            "  LLM_MODEL=gpt-4\n\n"
            f"Expected .env file location: {_ENV_SEARCH_PATHS[0]}"
        )

    return AppConfig()


def save_config(config: AppConfig) -> None:
    """Save configuration to YAML file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(mode="json")
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def ensure_data_dir(config: AppConfig) -> Path:
    """Ensure the data directory exists and return its path."""
    data_dir = Path(config.data_dir).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
