"""Tests for configuration validation and helpful error messages."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from doc_gen.config.loader import load_config


class TestConfigValidation:
    """Test configuration loading with helpful error messages."""

    def test_missing_env_file_shows_helpful_message(self, tmp_path: Path) -> None:
        """Should provide clear guidance when .env file is missing."""
        # Ensure no .env file exists and no env vars are set
        with patch.dict(os.environ, {}, clear=False):
            # Remove LLM_API_KEY if present
            if "LLM_API_KEY" in os.environ:
                del os.environ["LLM_API_KEY"]

            # Mock _ENV_SEARCH_PATHS to point to non-existent locations
            with patch(
                "doc_gen.config.loader._ENV_SEARCH_PATHS", [tmp_path / ".env"]
            ):
                # Should not raise but return default config with empty API key
                config = load_config()

                # API key should be empty, indicating missing configuration
                assert config.llm.api_key == ""

    def test_missing_api_key_raises_clear_error(self, tmp_path: Path) -> None:
        """Should raise helpful error when API key is not configured."""
        from doc_gen.config.loader import ConfigError

        # Ensure no env vars and no config file
        with patch.dict(os.environ, {}, clear=False):
            if "LLM_API_KEY" in os.environ:
                del os.environ["LLM_API_KEY"]

            with patch("doc_gen.config.loader.CONFIG_FILE", tmp_path / "nonexistent.yaml"):
                with patch(
                    "doc_gen.config.loader._ENV_SEARCH_PATHS", [tmp_path / ".env"]
                ):
                    # Should raise ConfigError with helpful message
                    with pytest.raises(ConfigError) as exc_info:
                        load_config(require_api_key=True)

                    error_msg = str(exc_info.value)
                    assert "API key" in error_msg.lower() or "configured" in error_msg.lower()

    def test_env_file_path_hint(self, tmp_path: Path, caplog) -> None:
        """Should hint about expected .env file location when missing."""
        import logging

        # Ensure no env vars
        with patch.dict(os.environ, {}, clear=False):
            if "LLM_API_KEY" in os.environ:
                del os.environ["LLM_API_KEY"]

            expected_path = tmp_path / ".env"

            with patch(
                "doc_gen.config.loader._ENV_SEARCH_PATHS", [expected_path]
            ):
                # Capture log output
                with caplog.at_level(logging.WARNING):
                    load_config()

                # Should warn about missing .env file
                assert any(".env" in record.message for record in caplog.records)


class TestConfigFromEnv:
    """Test configuration loaded from environment variables."""

    def test_api_key_from_env(self) -> None:
        """Should load API key from environment."""
        with patch.dict(
            os.environ,
            {"LLM_API_KEY": "sk-test-key", "LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4"},
        ):
            config = load_config()
            assert config.llm.api_key == "sk-test-key"
            assert config.llm.provider.value == "openai"
            assert config.llm.model == "gpt-4"

    def test_provider_case_insensitive(self) -> None:
        """Provider name should be case-insensitive."""
        with patch.dict(
            os.environ,
            {"LLM_API_KEY": "test", "LLM_PROVIDER": "OPENAI"},
        ):
            config = load_config()
            assert config.llm.provider.value == "openai"

    def test_unknown_provider_defaults_to_compatible(self) -> None:
        """Unknown provider should default to openai_compatible."""
        with patch.dict(
            os.environ,
            {"LLM_API_KEY": "test", "LLM_PROVIDER": "custom_provider"},
        ):
            config = load_config()
            assert config.llm.provider.value == "openai_compatible"
