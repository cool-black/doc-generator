"""Tests for configuration system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from doc_gen.config.loader import _process_env_vars, _substitute_env_vars, load_config, save_config
from doc_gen.config.models import AppConfig, LLMConfig, LLMProvider


def test_default_config():
    config = AppConfig()
    assert config.llm.provider == LLMProvider.OPENAI
    assert config.llm.timeout == 120
    assert config.log_level == "INFO"


def test_llm_config_defaults():
    cfg = LLMConfig(provider=LLMProvider.OPENAI)
    assert cfg.get_base_url() == "https://api.openai.com/v1"
    assert cfg.get_model() == "gpt-4o"


def test_llm_config_custom_url():
    cfg = LLMConfig(provider=LLMProvider.OPENAI, base_url="http://localhost:8080")
    assert cfg.get_base_url() == "http://localhost:8080"


def test_env_var_substitution():
    os.environ["TEST_KEY_123"] = "hello"
    assert _substitute_env_vars("${TEST_KEY_123}") == "hello"
    assert _substitute_env_vars("$TEST_KEY_123") == "hello"
    del os.environ["TEST_KEY_123"]


def test_process_env_vars():
    os.environ["MY_VAR"] = "world"
    data = {"key": "${MY_VAR}", "nested": {"inner": "$MY_VAR"}, "num": 42}
    result = _process_env_vars(data)
    assert result["key"] == "world"
    assert result["nested"]["inner"] == "world"
    assert result["num"] == 42
    del os.environ["MY_VAR"]


def test_save_and_load_config():
    # Isolate from .env file by patching _load_dotenv to no-op
    saved_key = os.environ.pop("LLM_API_KEY", None)
    saved_provider = os.environ.pop("LLM_PROVIDER", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.yaml"

            config = AppConfig(log_level="DEBUG")
            config.llm.api_key = "test-key"

            with patch("doc_gen.config.loader.CONFIG_DIR", config_dir), \
                 patch("doc_gen.config.loader.CONFIG_FILE", config_file), \
                 patch("doc_gen.config.loader._load_dotenv"):
                save_config(config)
                loaded = load_config()

            assert loaded.log_level == "DEBUG"
            assert loaded.llm.api_key == "test-key"
    finally:
        if saved_key is not None:
            os.environ["LLM_API_KEY"] = saved_key
        if saved_provider is not None:
            os.environ["LLM_PROVIDER"] = saved_provider


def test_load_config_missing_file():
    saved_key = os.environ.pop("LLM_API_KEY", None)
    saved_provider = os.environ.pop("LLM_PROVIDER", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "nonexistent.yaml"
            with patch("doc_gen.config.loader.CONFIG_FILE", config_file), \
                 patch("doc_gen.config.loader._load_dotenv"):
                config = load_config()
            assert config.llm.provider == LLMProvider.OPENAI
    finally:
        if saved_key is not None:
            os.environ["LLM_API_KEY"] = saved_key
        if saved_provider is not None:
            os.environ["LLM_PROVIDER"] = saved_provider
