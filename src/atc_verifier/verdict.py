"""Assemble a final verdict from the comparator's discrepancy list.

A readback either matches the instruction (``MATCH``) or it does not
(``DISCREPANCY``), in which case we carry the full, ordered list of problems.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .compare import Discrepancy
from .schema import ExtractedFields

MATCH = "MATCH"
DISCREPANCY = "DISCREPANCY"


@dataclass
class Verdict:
    """The outcome of comparing one instruction/readback pair."""

    status: str  # "MATCH" or "DISCREPANCY"
    discrepancies: list[Discrepancy] = field(default_factory=list)

    @property
    def is_match(self) -> bool:
        return self.status == MATCH

    @property
    def affected_fields(self) -> list[str]:
        """Distinct fields involved in discrepancies, in order of appearance."""
        seen: list[str] = []
        for d in self.discrepancies:
            if d.field not in seen:
                seen.append(d.field)
        return seen

    @property
    def categories(self) -> list[str]:
        """Distinct discrepancy categories, in order of appearance."""
        seen: list[str] = []
        for d in self.discrepancies:
            if d.category not in seen:
                seen.append(d.category)
        return seen

    def summary(self) -> str:
        if self.is_match:
            return "MATCH: readback is correct."
        lines = [f"DISCREPANCY: {len(self.discrepancies)} issue(s) found:"]
        lines += [f"  • {d.detail}" for d in self.discrepancies]
        return "\n".join(lines)


def build_verdict(discrepancies: list[Discrepancy]) -> Verdict:
    """A readback matches iff there are no discrepancies."""
    status = MATCH if not discrepancies else DISCREPANCY
    return Verdict(status=status, discrepancies=list(discrepancies))


@dataclass
class VerificationResult:
    """Everything produced for one instruction/readback pair.

    Carries the raw inputs, the two extracted-field objects (useful for the UI
    and for failure analysis), and the final verdict.
    """

    instruction_text: str
    readback_text: str
    instruction_fields: ExtractedFields
    readback_fields: ExtractedFields
    verdict: Verdict

    @property
    def status(self) -> str:
        return self.verdict.status

    def to_dict(self) -> dict:
        """JSON-serializable view (for eval logs / API responses)."""
        return {
            "instruction": self.instruction_text,
            "readback": self.readback_text,
            "status": self.verdict.status,
            "affected_fields": self.verdict.affected_fields,
            "categories": self.verdict.categories,
            "discrepancies": [
                {
                    "field": d.field,
                    "category": d.category,
                    "instructed": d.instructed,
                    "read_back": d.read_back,
                    "detail": d.detail,
                }
                for d in self.verdict.discrepancies
            ],
            "instruction_fields": self.instruction_fields.raw,
            "readback_fields": self.readback_fields.raw,
        }
