"""Hosted extraction backend using the Hugging Face Inference API.

Used by the live Streamlit Cloud demo, where the 1 GB free tier cannot run a
local model. Requires a free Hugging Face access token (Read scope) in the
``HF_TOKEN`` environment variable (or a Streamlit secret).

The served model is configurable via ``MODEL_NAME`` because free-tier model
availability changes over time; the default is ``Qwen/Qwen2.5-7B-Instruct``.
"""

from __future__ import annotations

import os

from .base import Extractor

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


class HuggingFaceExtractor(Extractor):
    name = "hf"

    def __init__(
        self,
        model: str | None = None,
        token: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: float = 60.0,
    ) -> None:
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "The 'huggingface_hub' package is required for the HF backend. "
                "Install it with `pip install huggingface_hub`."
            ) from exc

        self.model = model or os.getenv("MODEL_NAME", DEFAULT_MODEL)
        token = token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not token:
            raise RuntimeError(
                "The HF backend needs a token. Set HF_TOKEN to a free Hugging Face "
                "access token (Read scope) in your .env file or Streamlit secrets."
            )
        # A timeout stops a cold-starting / unreachable HF endpoint from hanging
        # the hosted demo indefinitely on a single click.
        self._client = InferenceClient(model=self.model, token=token, timeout=timeout)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _complete(self, prompt: str) -> str:
        out = self._client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        try:
            return out.choices[0].message.content or ""
        except (AttributeError, IndexError, KeyError):  # pragma: no cover - defensive
            return ""
