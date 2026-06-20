"""Local extraction backend using Ollama.

Runs a small instruction model on the user's machine (default
``qwen2.5:3b``). This is the backend used for development and for the
reproducible evaluation run: it is offline, free, and pinned to a specific
model tag, so results do not drift.

Requires the Ollama service to be running and the model pulled::

    ollama pull qwen2.5:3b
"""

from __future__ import annotations

import os

from .base import Extractor

DEFAULT_MODEL = "qwen2.5:3b"


class OllamaExtractor(Extractor):
    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        temperature: float = 0.0,
        timeout: float = 60.0,
    ) -> None:
        try:
            import ollama
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "The 'ollama' package is required for the local backend. "
                "Install it with `pip install ollama` and run `ollama pull qwen2.5:3b`."
            ) from exc

        self.model = model or os.getenv("MODEL_NAME", DEFAULT_MODEL)
        host = host or os.getenv("OLLAMA_HOST")
        # A timeout stops a hung/unreachable Ollama from blocking the request
        # (and the Streamlit spinner) indefinitely.
        self._client = ollama.Client(host=host, timeout=timeout)
        self.temperature = temperature

    def _complete(self, prompt: str) -> str:
        resp = self._client.generate(
            model=self.model,
            prompt=prompt,
            stream=False,
            options={"temperature": self.temperature},
        )
        # ollama responses support both attribute and dict-style access; be safe.
        text = getattr(resp, "response", "")
        if not text and isinstance(resp, dict):
            text = resp.get("response", "")
        return text or ""
