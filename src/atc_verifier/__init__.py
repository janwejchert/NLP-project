"""ATC Readback Verifier — public API.

Typical use::

    from atc_verifier import verify

    result = verify(
        "Speedbird 245, climb flight level 280.",
        "Climb flight level 280, Speedbird 245.",
    )
    print(result.status)            # "MATCH"
    print(result.verdict.summary())

By default this uses the extractor backend named by the ``EXTRACTOR_BACKEND``
environment variable (``ollama`` locally, ``hf`` for the hosted demo). Pass a
pre-built ``extractor`` to reuse one across many calls (e.g. an eval loop).
"""

from __future__ import annotations

from .compare import Discrepancy, compare_fields
from .extract.base import Extractor, get_extractor
from .schema import Altitude, ExtractedFields, Heading, Runway
from .verdict import Verdict, VerificationResult, build_verdict

__all__ = [
    "verify",
    "VerificationResult",
    "Verdict",
    "Discrepancy",
    "ExtractedFields",
    "Altitude",
    "Heading",
    "Runway",
    "Extractor",
    "get_extractor",
    "compare_fields",
]

__version__ = "0.1.0"


def verify(
    instruction: str,
    readback: str,
    extractor: Extractor | None = None,
) -> VerificationResult:
    """Verify a pilot readback against a controller instruction.

    Steps: extract structured fields from each message (LLM), compare them
    field-by-field (deterministic), and assemble a verdict.
    """
    extractor = extractor or get_extractor()
    instruction_fields = extractor.extract(instruction)
    readback_fields = extractor.extract(readback)
    discrepancies = compare_fields(instruction_fields, readback_fields)
    verdict = build_verdict(discrepancies)
    return VerificationResult(
        instruction_text=instruction,
        readback_text=readback,
        instruction_fields=instruction_fields,
        readback_fields=readback_fields,
        verdict=verdict,
    )
