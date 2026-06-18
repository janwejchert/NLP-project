"""Typed field schema for ATC instructions and readbacks.

The extraction step (an LLM) turns free text into one :class:`ExtractedFields`
object. The comparator (``compare.py``) then works purely on these typed,
*normalized* values, so all downstream logic is deterministic and testable
without any model in the loop.

We track eight fields, matching the project proposal and the labelled test set:
``callsign, altitude, heading, speed, frequency, squawk, runway, qnh``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Canonical, ordered list of comparable fields. The comparator iterates this.
# ``callsign`` is handled specially (it is the aircraft identity), but it is
# still part of the schema and the comparison.
FIELD_NAMES: tuple[str, ...] = (
    "callsign",
    "altitude",
    "heading",
    "speed",
    "frequency",
    "squawk",
    "runway",
    "qnh",
)


# --------------------------------------------------------------------------- #
# Sub-structures for the fields that carry more than a single scalar.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Altitude:
    """An altitude clearance.

    ``kind`` distinguishes a flight level (``"FL"``, e.g. FL280) from an
    altitude in feet (``"ALT"``, e.g. 3000 ft). ``value`` is the numeric part
    (the flight-level number, or the number of feet).
    """

    kind: str  # "FL" or "ALT"
    value: int

    def human(self) -> str:
        return f"FL{self.value}" if self.kind == "FL" else f"{self.value} ft"


@dataclass(frozen=True)
class Heading:
    """A heading in degrees, with an optional turn direction."""

    value: int
    direction: str | None = None  # "left" | "right" | None

    def human(self) -> str:
        d = f"{self.direction} " if self.direction else ""
        return f"{d}heading {self.value:03d}"


@dataclass(frozen=True)
class Runway:
    """A runway designator: a number plus an optional side."""

    number: str
    side: str | None = None  # "left" | "right" | "center" | None

    def human(self) -> str:
        s = f" {self.side}" if self.side else ""
        return f"runway {self.number}{s}"


# --------------------------------------------------------------------------- #
# Normalization helpers — keep all "are these the same?" logic in one place so
# semantically-equal readbacks compare equal (units, trailing zeros, spelling).
# --------------------------------------------------------------------------- #
def normalize_callsign(value: str | None) -> str | None:
    """Lower-case, strip punctuation/extra spaces. ``None`` stays ``None``.

    Telephony spelling differences that matter (``245`` vs ``254``,
    ``Quebec`` vs ``Golf``) are preserved as different strings on purpose so
    the comparator flags them.
    """
    if value is None:
        return None
    v = value.strip().lower()
    v = v.replace("-", " ")
    v = re.sub(r"[^a-z0-9 ]", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v or None


def normalize_frequency(value: Any | None) -> str | None:
    """Canonicalize a radio frequency to a trimmed decimal string.

    ``118.7`` and ``118.70`` and ``"118.700"`` all become ``"118.7"``.
    """
    if value is None:
        return None
    s = str(value).strip().replace(",", ".")
    s = re.sub(r"[^0-9.]", "", s)
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return s
    # Trim trailing zeros without losing precision (118.70 -> 118.7, 118 -> 118).
    text = f"{f:.3f}".rstrip("0").rstrip(".")
    return text


def normalize_squawk(value: Any | None) -> str | None:
    """A transponder code: 4 octal digits, leading zeros preserved."""
    if value is None:
        return None
    s = re.sub(r"\D", "", str(value))
    if not s:
        return None
    return s.zfill(4) if len(s) <= 4 else s


def digits_of(value: Any) -> str:
    """Return just the digit characters of a value (for transposition checks)."""
    return re.sub(r"\D", "", str(value))


@dataclass
class ExtractedFields:
    """All fields extracted from one message (instruction *or* readback).

    Every field is ``Optional``; ``None`` means "not present in this message".
    Instances are built from the LLM's JSON via :meth:`from_json`, which also
    normalizes scalar fields.
    """

    callsign: str | None = None
    altitude: Altitude | None = None
    heading: Heading | None = None
    speed: int | None = None
    frequency: str | None = None
    squawk: str | None = None
    runway: Runway | None = None
    qnh: int | None = None
    # Kept for debugging / failure analysis: the raw JSON the model returned.
    raw: dict[str, Any] = field(default_factory=dict)

    # ----------------------------------------------------------------- #
    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ExtractedFields:
        """Build (and normalize) fields from a model's JSON output.

        Lenient by design: missing keys, ``null`` values, and minor type
        slop (a string where an int is expected) are all tolerated.
        """
        data = data or {}

        def _int(x: Any) -> int | None:
            if x is None:
                return None
            # Parse via float so decimal/sign slop ("250.4", "-30") rounds to a
            # sensible int instead of having its point/sign stripped and the bare
            # digits concatenated ("250.4" -> 2504). Falls back to digit-only.
            cleaned = re.sub(r"[^0-9.\-]", "", str(x))
            try:
                return int(round(float(cleaned)))
            except (ValueError, OverflowError):
                d = digits_of(x)
                return int(d) if d else None

        # altitude: {"kind": "FL"|"ALT", "value": int}
        altitude = None
        alt = data.get("altitude")
        if isinstance(alt, dict) and alt.get("value") is not None:
            kind = str(alt.get("kind", "FL")).upper()
            kind = "FL" if kind not in ("FL", "ALT") else kind
            val = _int(alt.get("value"))
            if val is not None:
                altitude = Altitude(kind=kind, value=val)

        # heading: {"value": int, "direction": "left"|"right"|null}
        heading = None
        hdg = data.get("heading")
        if isinstance(hdg, dict) and hdg.get("value") is not None:
            val = _int(hdg.get("value"))
            if val is not None:
                direction = hdg.get("direction")
                direction = direction.lower() if isinstance(direction, str) else None
                heading = Heading(value=val, direction=direction)

        # runway: {"number": str, "side": "left"|"right"|"center"|null}
        runway = None
        rwy = data.get("runway")
        if isinstance(rwy, dict):
            raw_number = "" if rwy.get("number") is None else str(rwy.get("number")).strip()
            side = rwy.get("side")
            side = side.lower() if isinstance(side, str) and side.strip() else None
            # A single-token designator may pack the side, e.g. "06L" / "24 R".
            # Split it off so a left/right read-back error is not silently lost;
            # the explicit ``side`` key still wins if both are present.
            m = re.match(r"^\s*(\d+)\s*([LRC])\s*$", raw_number, re.IGNORECASE)
            if m:
                raw_number = m.group(1)
                side = side or {"L": "left", "R": "right", "C": "center"}[m.group(2).upper()]
            number = digits_of(raw_number) or raw_number
            if number:  # a blank / whitespace-only number means "no runway"
                # Canonicalize a single-digit runway to two digits ("6" or int 6 ->
                # "06"). ICAO runways are 01-36 and single-digit designators are
                # written zero-padded, so a dropped pad on one side is a formatting
                # artifact, not a real read-back error. Non-numeric values untouched.
                if number.isdigit() and len(number) == 1:
                    number = number.zfill(2)
                runway = Runway(number=number, side=side)

        return cls(
            callsign=normalize_callsign(data.get("callsign")),
            altitude=altitude,
            heading=heading,
            speed=_int(data.get("speed")),
            frequency=normalize_frequency(data.get("frequency")),
            squawk=normalize_squawk(data.get("squawk")),
            runway=runway,
            qnh=_int(data.get("qnh")),
            raw=data,
        )

    # ----------------------------------------------------------------- #
    def get(self, name: str) -> Any:
        """Field accessor by canonical name (used by the comparator)."""
        return getattr(self, name)

    def human(self, name: str) -> str:
        """Readable rendering of one field's value, for detail messages."""
        value = self.get(name)
        if value is None:
            return "none"
        if isinstance(value, (Altitude, Heading, Runway)):
            return value.human()
        return str(value)
