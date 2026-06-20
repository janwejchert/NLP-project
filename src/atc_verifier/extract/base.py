"""Extractor interface + a factory + shared JSON-parsing helpers.

An :class:`Extractor` turns one message (instruction *or* readback) into an
:class:`~atc_verifier.schema.ExtractedFields`. Concrete backends live next to
this file (``ollama_backend.py``, ``hf_backend.py``); they only need to call a
model and return its raw text, all JSON cleanup and field normalization is
shared here so the two backends behave identically.
"""

from __future__ import annotations

import abc
import json
import os
import re
from pathlib import Path
from typing import Any

from ..schema import ExtractedFields

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str = "extract_fields.txt") -> str:
    """Read a versioned prompt template from the ``prompts/`` directory."""
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def parse_model_json(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from a model's text response.

    Small instruction models sometimes wrap JSON in prose or code fences. We
    strip fences, grab the first balanced ``{...}`` block, and parse it. On
    total failure we return ``{}`` (an all-``None`` extraction) rather than
    raising, so one bad response never crashes a whole eval run.
    """
    if not text:
        return {}
    cleaned = text.strip()
    # Remove ```json ... ``` / ``` ... ``` fences.
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    # Fast path. Only accept an object; a top-level array/scalar (e.g. ``[...]``
    # or ``"none"``) falls through so we can hunt for an embedded object and
    # never hand a non-dict to ExtractedFields.from_json.
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    # Fallback: scan for the first JSON object embedded in prose. We try
    # ``raw_decode`` at each "{" so brace matching respects string literals
    # (a "}" inside a value no longer mis-balances) and a non-parsing earlier
    # block (e.g. a "{field: value}" schema hint in the prose) does not abort
    # the search for the real object later in the text.
    decoder = json.JSONDecoder()
    idx = cleaned.find("{")
    while idx != -1:
        try:
            obj = decoder.raw_decode(cleaned, idx)[0]
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        idx = cleaned.find("{", idx + 1)
    return {}


class Extractor(abc.ABC):
    """Turns text into structured :class:`ExtractedFields`."""

    #: Human-readable backend name, set by subclasses.
    name: str = "base"

    @abc.abstractmethod
    def _complete(self, prompt: str) -> str:
        """Send ``prompt`` to the model and return its raw text completion."""

    def extract(self, text: str) -> ExtractedFields:
        """Extract and normalize fields from one message.

        The default implementation builds the prompt, calls the model once,
        retries once with a stricter nudge if the JSON is unusable, and then
        normalizes via :meth:`ExtractedFields.from_json`.
        """
        template = load_prompt()
        prompt = template.replace("{{MESSAGE}}", text.strip())
        raw = self._complete(prompt)
        data = parse_model_json(raw)
        if not data:
            # One stricter retry: many small models recover when told "JSON only".
            raw = self._complete(prompt + "\n\nReturn ONLY the JSON object, nothing else.")
            data = parse_model_json(raw)
        return ExtractedFields.from_json(data)


def get_extractor(backend: str | None = None, **kwargs: Any) -> Extractor:
    """Factory: return the configured extractor backend.

    ``backend`` defaults to the ``EXTRACTOR_BACKEND`` env var, then ``"ollama"``.
    Backends are imported lazily so the app never needs both sets of
    dependencies installed at once.
    """
    backend = (backend or os.getenv("EXTRACTOR_BACKEND", "ollama")).lower()
    if backend == "ollama":
        from .ollama_backend import OllamaExtractor

        return OllamaExtractor(**kwargs)
    if backend in ("hf", "huggingface"):
        from .hf_backend import HuggingFaceExtractor

        return HuggingFaceExtractor(**kwargs)
    raise ValueError(
        f"Unknown EXTRACTOR_BACKEND '{backend}'. Use 'ollama' or 'hf'."
    )
