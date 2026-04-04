from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable
from urllib import error, request

from .config import (
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_MAX_OUTPUT_TOKENS,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_LLM_TIMEOUT_SECONDS,
)


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value is None:
            continue
        stripped = value.strip()
        if stripped:
            return stripped
    return None


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    base_url: str = DEFAULT_LLM_BASE_URL
    model: str = DEFAULT_LLM_MODEL
    timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS
    temperature: float = DEFAULT_LLM_TEMPERATURE
    max_output_tokens: int = DEFAULT_LLM_MAX_OUTPUT_TOKENS

    @classmethod
    def from_env(
        cls,
        *,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> "LLMSettings | None":
        api_key = _first_non_empty(
            os.getenv("CODEBASE_COPILOT_LLM_API_KEY"),
            os.getenv("OPENAI_API_KEY"),
        )
        if not api_key:
            return None

        resolved_base_url = _first_non_empty(
            base_url,
            os.getenv("CODEBASE_COPILOT_LLM_BASE_URL"),
            os.getenv("OPENAI_BASE_URL"),
            DEFAULT_LLM_BASE_URL,
        )
        resolved_model = _first_non_empty(
            model,
            os.getenv("CODEBASE_COPILOT_LLM_MODEL"),
            os.getenv("OPENAI_MODEL"),
            DEFAULT_LLM_MODEL,
        )
        resolved_timeout = timeout_seconds
        if resolved_timeout is None:
            env_timeout = _first_non_empty(os.getenv("CODEBASE_COPILOT_LLM_TIMEOUT_SECONDS"))
            resolved_timeout = float(env_timeout) if env_timeout is not None else DEFAULT_LLM_TIMEOUT_SECONDS

        return cls(
            api_key=api_key,
            base_url=str(resolved_base_url).rstrip("/"),
            model=str(resolved_model),
            timeout_seconds=float(resolved_timeout),
        )


class LLMRequestError(RuntimeError):
    """Raised when the configured LLM request fails."""


class OpenAICompatibleChatSynthesizer:
    """Minimal OpenAI-compatible chat client used for Day 4 answers."""

    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def _build_payload(self, prompt: str, *, stream: bool) -> bytes:
        payload = {
            "model": self.settings.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_output_tokens,
        }
        if stream:
            payload["stream"] = True
        return json.dumps(payload).encode("utf-8")

    def _build_request(self, body: bytes) -> request.Request:
        api_request = request.Request(
            url=f"{self.settings.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return api_request

    @staticmethod
    def _extract_response_text(message: object) -> str:
        if isinstance(message, str):
            return message.strip()

        if isinstance(message, list):
            text_blocks: list[str] = []
            for block in message:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = str(block.get("text", "")).strip()
                    if text:
                        text_blocks.append(text)
            if text_blocks:
                return "\n".join(text_blocks)

        return ""

    @staticmethod
    def _extract_stream_chunk(payload: dict[str, object]) -> str:
        try:
            choice = payload["choices"][0]
        except (KeyError, IndexError, TypeError):
            return ""

        if isinstance(choice, dict):
            delta = choice.get("delta")
            if isinstance(delta, dict) and "content" in delta:
                content = delta["content"]
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    text_parts: list[str] = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = str(item.get("text", ""))
                            if text:
                                text_parts.append(text)
                    return "".join(text_parts)

            message = choice.get("message")
            if message is not None:
                return OpenAICompatibleChatSynthesizer._extract_response_text(message)

        return ""

    def generate(self, prompt: str) -> str:
        body = self._build_payload(prompt, stream=False)
        api_request = self._build_request(body)

        try:
            with request.urlopen(api_request, timeout=self.settings.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
            raise LLMRequestError(f"LLM HTTP error {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise LLMRequestError(f"LLM connection error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMRequestError("LLM request timed out") from exc

        try:
            message = response_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMRequestError("LLM response did not include a chat completion message") from exc

        content = self._extract_response_text(message)
        if content:
            return content

        raise LLMRequestError("LLM response content was empty")

    def generate_stream(self, prompt: str) -> Iterable[str]:
        body = self._build_payload(prompt, stream=True)
        api_request = self._build_request(body)

        try:
            with request.urlopen(api_request, timeout=self.settings.timeout_seconds) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    payload_text = line[5:].strip()
                    if payload_text == "[DONE]":
                        break
                    try:
                        payload = json.loads(payload_text)
                    except json.JSONDecodeError as exc:
                        raise LLMRequestError("LLM streaming response contained invalid JSON") from exc

                    chunk = self._extract_stream_chunk(payload)
                    if chunk:
                        yield chunk
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
            raise LLMRequestError(f"LLM HTTP error {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise LLMRequestError(f"LLM connection error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMRequestError("LLM request timed out") from exc
