"""Unified LLM client interface."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from doc_gen.config.models import LLMConfig, LLMProvider

logger = logging.getLogger(__name__)


class LLMResponse:
    def __init__(self, content: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class LLMClient:
    """Unified async LLM client supporting multiple providers."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client

    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """Generate text from the LLM with retry logic."""
        temp = temperature if temperature is not None else self.config.temperature
        last_error: Exception | None = None

        logger.debug("LLM generate: prompt_len=%d, system_len=%d, max_tokens=%s, temp=%s",
                     len(prompt), len(system), max_tokens, temp)

        for attempt in range(self.config.max_retries + 1):
            try:
                if self.config.uses_openai_protocol():
                    return await self._call_openai_compatible(prompt, system, max_tokens, temp)
                else:
                    return await self._call_anthropic(prompt, system, max_tokens, temp)
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                # Don't retry 4xx client errors (except 429 rate limit)
                if isinstance(e, httpx.HTTPStatusError) and 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    detail = e.response.text[:500]
                    logger.error("LLM client error %s: %s", e.response.status_code, detail)
                    raise RuntimeError(f"HTTP {e.response.status_code}: {detail}") from e
                if attempt < self.config.max_retries:
                    wait = 2 ** attempt
                    logger.warning("LLM request failed (attempt %d/%d), retrying in %ds: %s",
                                   attempt + 1, self.config.max_retries + 1, wait, e)
                    import asyncio
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"LLM call failed after {self.config.max_retries + 1} attempts: {last_error}"
        )

    async def _call_openai_compatible(
        self, prompt: str, system: str, max_tokens: int | None, temperature: float
    ) -> LLMResponse:
        base_url = self.config.get_base_url()
        model = self.config.get_model()

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        logger.debug("OpenAI API request: model=%s, messages=%d, temp=%s, max_tokens=%s",
                     model, len(messages), temperature, max_tokens)

        resp = await self.client.post(
            f"{base_url}/chat/completions",
            json=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )

        if resp.status_code >= 400:
            logger.error("OpenAI API error %s: %s", resp.status_code, resp.text[:500])

        resp.raise_for_status()
        data = resp.json()

        message = data["choices"][0]["message"]
        content = message.get("content") or ""
        # Some reasoning models (e.g. kimi-k2.5) put output in reasoning_content
        if not content.strip() and message.get("reasoning_content"):
            content = message["reasoning_content"]
        usage = data.get("usage", {})
        logger.debug("OpenAI API response: prompt_tokens=%s, completion_tokens=%s, content_len=%d",
                     usage.get("prompt_tokens"), usage.get("completion_tokens"), len(content))
        return LLMResponse(
            content=content,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )

    async def _call_anthropic(
        self, prompt: str, system: str, max_tokens: int | None, temperature: float
    ) -> LLMResponse:
        base_url = self.config.get_base_url()
        model = self.config.get_model()

        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        if system:
            body["system"] = system

        resp = await self.client.post(
            f"{base_url}/messages",
            json=body,
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        content = "".join(
            block["text"] for block in data["content"] if block["type"] == "text"
        )
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
        )

    async def check_connection(self) -> tuple[bool, str]:
        """Test API connectivity with a minimal request. Returns (success, message)."""
        try:
            response = await self.generate(
                prompt="Hi, reply with just the word 'ok'.",
                max_tokens=200,  # Some models (reasoning models) need more tokens
            )
            if response.content.strip():
                return True, f"API connected. Model response: {response.content.strip()[:50]}"
            return False, "API returned empty response."
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 401:
                return False, "Authentication failed: invalid API key."
            elif status == 404:
                return False, f"Endpoint not found. Check base URL: {self.config.get_base_url()}"
            elif status == 429:
                return True, "API connected (rate limited, but key is valid)."
            else:
                body = e.response.text[:200]
                return False, f"HTTP {status}: {body}"
        except httpx.ConnectError:
            return False, f"Cannot connect to {self.config.get_base_url()}. Check URL and network."
        except httpx.TimeoutException:
            return False, f"Connection timed out ({self.config.timeout}s). Check URL and network."
        except Exception as e:
            return False, f"Unexpected error: {e}"

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
