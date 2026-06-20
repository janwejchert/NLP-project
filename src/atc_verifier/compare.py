"""Deterministic field-by-field comparator: the core of the verifier.

This module contains **no LLM calls**. It takes the structured fields extracted
from the controller instruction and from the pilot readback and decides, for
each field, whether the readback is correct. Every discrepancy is classified
into one of the categories observed in our test set:

* ``value_substitution`` – a value was read back, but a *different* one.
* ``digit_transposition`` – the read-back value uses the *same digits* in a
  different order (a distinct, higher-risk failure mode, e.g. runway 21 -> 12).
* ``omission``           – a required item from the instruction was not read back.
* ``callsign_error``     – the callsign is wrong or missing.
* ``added_element``      – the readback contains an item that was not instructed.

Because this logic is ours and fully deterministic, it is unit-tested directly
(see ``tests/test_compare.py``) and is defensible item-by-item in the Q&A.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schema import FIELD_NAMES, ExtractedFields, digits_of

# Discrepancy categories (also the labels used in the gold test set).
VALUE_SUBSTITUTION = "value_substitution"
DIGIT_TRANSPOSITION = "digit_transposition"
OMISSION = "omission"
CALLSIGN_ERROR = "callsign_error"
ADDED_ELEMENT = "added_element"


@dataclass(frozen=True)
class Discrepancy:
    """A single problem found while comparing a readback to an instruction."""

    field: str  # affected field, e.g. "altitude"
    category: str  # one of the category constants above
    instructed: str | None  # human-readable instructed value (or None)
    read_back: str | None  # human-readable read-back value (or None)
    detail: str  # one-line explanation, mirrors the test set's expected_detail

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"[{self.category}] {self.field}: {self.detail}"


def _values_equal(name: str, a: Any, b: Any) -> bool:
    """Equality on normalized field values.

    Fields are already normalized by :meth:`ExtractedFields.from_json`, so for
    most fields this is a plain ``==``. Sub-structures compare by their relevant
    parts (heading/runway ignore nothing here because they are frozen
    dataclasses and compare field-by-field).
    """
    return a == b


def _is_transposition(a: Any, b: Any) -> bool:
    """True iff ``a`` and ``b`` differ only by the *order* of their digits.

    This cleanly separates a transposition (squawk 5701 -> 5071, freq
    119.45 -> 119.54, runway 21 -> 12) from an ordinary value substitution
    (FL240 -> FL250), because a substitution changes the multiset of digits.
    """
    da, db = digits_of(a), digits_of(b)
    if not da or not db:
        return False
    return da != db and sorted(da) == sorted(db)


def _described(fields: ExtractedFields, name: str) -> str:
    """Field value prefixed by its name for a detail message.

    Scalar fields render bare ("FL240", "250"), so we prefix the field noun:
    "altitude FL240". Structured fields (heading, runway) already include the
    noun in their own ``human()`` output ("heading 270", "runway 24 left"), so we
    do not prefix again, avoiding "heading heading 270" / "runway runway 24".
    """
    text = fields.human(name)
    return text if name in text.split() else f"{name} {text}"


def _compare_callsign(instruction: ExtractedFields, readback: ExtractedFields) -> list[Discrepancy]:
    """The callsign is the aircraft's identity; any mismatch is a callsign error
    regardless of whether the digits happen to be a transposition."""
    inst, rb = instruction.callsign, readback.callsign
    if inst is None:
        # No callsign instructed (unusual); nothing to verify.
        return []
    if rb is None:
        return [
            Discrepancy(
                field="callsign",
                category=CALLSIGN_ERROR,
                instructed=inst,
                read_back=None,
                detail="no callsign in readback",
            )
        ]
    if inst != rb:
        return [
            Discrepancy(
                field="callsign",
                category=CALLSIGN_ERROR,
                instructed=inst,
                read_back=rb,
                detail=f"callsign read back as '{rb}' instead of '{inst}'",
            )
        ]
    return []


def _compare_runway(instruction: ExtractedFields, readback: ExtractedFields) -> list[Discrepancy]:
    """A runway clearance is identified by its number; the L/R/C side is a
    refinement. We compare on the number, and flag a *side* difference only when
    BOTH messages explicitly state a side. Rationale: an unstated side is not a
    read-back error, and small extraction models frequently hallucinate a side,
    so comparing a stated side against an absent/invented one produces false
    alarms rather than real safety findings.
    """
    inst, rb = instruction.runway, readback.runway
    if inst is not None and rb is None:
        return [
            Discrepancy("runway", OMISSION, instruction.human("runway"), None,
                        f"{_described(instruction, 'runway')} not read back")
        ]
    if inst is None and rb is not None:
        return [
            Discrepancy("runway", ADDED_ELEMENT, None, readback.human("runway"),
                        f"{_described(readback, 'runway')} read back but not instructed")
        ]
    if inst is None and rb is None:
        return []

    # Both present: compare the runway NUMBER first.
    if inst.number != rb.number:
        category = (
            DIGIT_TRANSPOSITION if _is_transposition(inst.number, rb.number) else VALUE_SUBSTITUTION
        )
        verb = "transposed to" if category == DIGIT_TRANSPOSITION else "read back as"
        return [
            Discrepancy("runway", category, instruction.human("runway"), readback.human("runway"),
                        f"instructed {_described(instruction, 'runway')}, "
                        f"{verb} {_described(readback, 'runway')}")
        ]
    # Numbers match: only a side stated in BOTH messages can be a discrepancy.
    if inst.side and rb.side and inst.side != rb.side:
        return [
            Discrepancy("runway", VALUE_SUBSTITUTION, instruction.human("runway"),
                        readback.human("runway"),
                        f"runway side instructed {inst.side}, read back {rb.side}")
        ]
    return []


def _compare_heading(instruction: ExtractedFields, readback: ExtractedFields) -> list[Discrepancy]:
    """A heading is identified by its degrees; the turn direction is a refinement.
    We compare on the value, and flag a *direction* difference only when BOTH
    messages explicitly state a direction, mirroring :func:`_compare_runway`.
    Rationale: an unstated turn direction is not a read-back error, and small
    extraction models frequently omit or hallucinate one, so comparing a stated
    direction against an absent/invented one produces false alarms rather than
    real safety findings.
    """
    inst, rb = instruction.heading, readback.heading
    if inst is not None and rb is None:
        return [
            Discrepancy("heading", OMISSION, instruction.human("heading"), None,
                        f"{_described(instruction, 'heading')} not read back")
        ]
    if inst is None and rb is not None:
        return [
            Discrepancy("heading", ADDED_ELEMENT, None, readback.human("heading"),
                        f"{_described(readback, 'heading')} read back but not instructed")
        ]
    if inst is None and rb is None:
        return []

    # Both present: compare the heading VALUE (degrees) first.
    if inst.value != rb.value:
        category = (
            DIGIT_TRANSPOSITION if _is_transposition(inst.value, rb.value) else VALUE_SUBSTITUTION
        )
        verb = "transposed to" if category == DIGIT_TRANSPOSITION else "read back as"
        return [
            Discrepancy("heading", category, instruction.human("heading"),
                        readback.human("heading"),
                        f"instructed {_described(instruction, 'heading')}, "
                        f"{verb} {_described(readback, 'heading')}")
        ]
    # Values match: only a direction stated in BOTH messages can be a discrepancy.
    if inst.direction and rb.direction and inst.direction != rb.direction:
        return [
            Discrepancy("heading", VALUE_SUBSTITUTION, instruction.human("heading"),
                        readback.human("heading"),
                        f"heading turn instructed {inst.direction}, read back {rb.direction}")
        ]
    return []


def compare_fields(
    instruction: ExtractedFields, readback: ExtractedFields
) -> list[Discrepancy]:
    """Compare an instruction against a readback and return all discrepancies.

    An empty list means the readback matches. The order of discrepancies
    follows :data:`schema.FIELD_NAMES` for stable, readable output.
    """
    discrepancies: list[Discrepancy] = []

    for name in FIELD_NAMES:
        if name == "callsign":
            discrepancies.extend(_compare_callsign(instruction, readback))
            continue

        if name == "runway":
            discrepancies.extend(_compare_runway(instruction, readback))
            continue

        if name == "heading":
            discrepancies.extend(_compare_heading(instruction, readback))
            continue

        inst = instruction.get(name)
        rb = readback.get(name)

        # Required item not read back.
        if inst is not None and rb is None:
            discrepancies.append(
                Discrepancy(
                    field=name,
                    category=OMISSION,
                    instructed=instruction.human(name),
                    read_back=None,
                    detail=f"{_described(instruction, name)} not read back",
                )
            )
            continue

        # Item read back that was never instructed.
        if inst is None and rb is not None:
            discrepancies.append(
                Discrepancy(
                    field=name,
                    category=ADDED_ELEMENT,
                    instructed=None,
                    read_back=readback.human(name),
                    detail=f"{_described(readback, name)} read back but not instructed",
                )
            )
            continue

        # Both absent: nothing to compare.
        if inst is None and rb is None:
            continue

        # Both present: equal or a value error (substitution vs transposition).
        if not _values_equal(name, inst, rb):
            category = (
                DIGIT_TRANSPOSITION if _is_transposition(inst, rb) else VALUE_SUBSTITUTION
            )
            verb = "transposed to" if category == DIGIT_TRANSPOSITION else "read back as"
            discrepancies.append(
                Discrepancy(
                    field=name,
                    category=category,
                    instructed=instruction.human(name),
                    read_back=readback.human(name),
                    detail=(
                        f"instructed {_described(instruction, name)}, "
                        f"{verb} {_described(readback, name)}"
                    ),
                )
            )

    return discrepancies
