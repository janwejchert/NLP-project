"""Unit tests for the deterministic comparator (the project's core IP).

These build ``ExtractedFields`` directly from JSON dicts, the same shape the
LLM emits, so they exercise both the normalization in ``schema.py`` and the
classification logic in ``compare.py`` with no model in the loop. Cases mirror
the categories in our gold test set (``eval/data/atc_readback_test_set.csv``).
"""

from __future__ import annotations

from atc_verifier import compare_fields
from atc_verifier.compare import (
    ADDED_ELEMENT,
    CALLSIGN_ERROR,
    DIGIT_TRANSPOSITION,
    OMISSION,
    VALUE_SUBSTITUTION,
)
from atc_verifier.schema import ExtractedFields
from atc_verifier.verdict import build_verdict


def fields(**kw) -> ExtractedFields:
    """Build normalized fields from a JSON-like dict (as the LLM would return)."""
    return ExtractedFields.from_json(kw)


def categories(inst, rb) -> list[str]:
    return [d.category for d in compare_fields(inst, rb)]


def affected(inst, rb) -> list[str]:
    return [d.field for d in compare_fields(inst, rb)]


# --------------------------------------------------------------------------- #
# MATCH cases
# --------------------------------------------------------------------------- #
def test_match_single_altitude_fl():
    inst = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 280})
    rb = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 280})
    assert compare_fields(inst, rb) == []
    assert build_verdict(compare_fields(inst, rb)).is_match


def test_match_multi_item():
    inst = fields(
        callsign="Speedbird 245",
        altitude={"kind": "FL", "value": 240},
        heading={"value": 270, "direction": "left"},
    )
    rb = fields(
        callsign="Speedbird 245",
        altitude={"kind": "FL", "value": 240},
        heading={"value": 270, "direction": "left"},
    )
    assert compare_fields(inst, rb) == []


def test_match_wind_is_informational():
    # Wind is never extracted, so a correct landing readback that omits wind matches.
    inst = fields(callsign="Vueling 38 Lima", runway={"number": "24"})
    rb = fields(callsign="Vueling 38 Lima", runway={"number": "24"})
    assert compare_fields(inst, rb) == []


def test_match_spelled_out_numbers_normalize():
    # "climb three thousand feet, QNH one zero one three" -> digits via the model;
    # from_json then yields ALT 3000 / qnh 1013 on both sides.
    inst = fields(callsign="G-CDEF", altitude={"kind": "ALT", "value": 3000}, qnh=1013)
    rb = fields(callsign="G-CDEF", altitude={"kind": "ALT", "value": 3000}, qnh=1013)
    assert compare_fields(inst, rb) == []


def test_match_frequency_trailing_zero():
    inst = fields(callsign="Ryanair 12 Quebec", frequency="118.7")
    rb = fields(callsign="Ryanair 12 Quebec", frequency="118.70")
    assert compare_fields(inst, rb) == []


def test_match_callsign_normalizes_case_and_punctuation():
    inst = fields(callsign="G-ABCD", altitude={"kind": "ALT", "value": 3000})
    rb = fields(callsign="g abcd", altitude={"kind": "ALT", "value": 3000})
    assert compare_fields(inst, rb) == []


# --------------------------------------------------------------------------- #
# value_substitution
# --------------------------------------------------------------------------- #
def test_value_substitution_altitude():
    inst = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 240})
    rb = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 250})
    assert categories(inst, rb) == [VALUE_SUBSTITUTION]
    assert affected(inst, rb) == ["altitude"]


def test_value_substitution_qnh():
    inst = fields(callsign="G-CDEF", altitude={"kind": "ALT", "value": 3000}, qnh=1013)
    rb = fields(callsign="G-CDEF", altitude={"kind": "ALT", "value": 3000}, qnh=1018)
    assert categories(inst, rb) == [VALUE_SUBSTITUTION]
    assert affected(inst, rb) == ["qnh"]


def test_two_simultaneous_value_errors():
    inst = fields(
        callsign="Speedbird 245",
        altitude={"kind": "FL", "value": 240},
        heading={"value": 270, "direction": "left"},
    )
    rb = fields(
        callsign="Speedbird 245",
        altitude={"kind": "FL", "value": 250},
        heading={"value": 250, "direction": "left"},
    )
    assert affected(inst, rb) == ["altitude", "heading"]
    assert categories(inst, rb) == [VALUE_SUBSTITUTION, VALUE_SUBSTITUTION]


# --------------------------------------------------------------------------- #
# digit_transposition
# --------------------------------------------------------------------------- #
def test_transposition_squawk():
    inst = fields(callsign="Easy 4471", squawk="5701")
    rb = fields(callsign="Easy 4471", squawk="5071")
    assert categories(inst, rb) == [DIGIT_TRANSPOSITION]


def test_transposition_frequency():
    inst = fields(callsign="Speedbird 245", frequency="119.45")
    rb = fields(callsign="Speedbird 245", frequency="119.54")
    assert categories(inst, rb) == [DIGIT_TRANSPOSITION]


def test_transposition_runway_reversal():
    inst = fields(callsign="Vueling 38 Lima", runway={"number": "21"})
    rb = fields(callsign="Vueling 38 Lima", runway={"number": "12"})
    assert categories(inst, rb) == [DIGIT_TRANSPOSITION]


def test_transposition_heading():
    inst = fields(callsign="Iberia 6020", heading={"value": 310, "direction": "right"})
    rb = fields(callsign="Iberia 6020", heading={"value": 130, "direction": "right"})
    assert categories(inst, rb) == [DIGIT_TRANSPOSITION]


def test_substitution_not_flagged_as_transposition():
    # Different digit multiset -> substitution, not transposition.
    inst = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 240})
    rb = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 250})
    assert categories(inst, rb) == [VALUE_SUBSTITUTION]


# --------------------------------------------------------------------------- #
# runway side (a stated side is compared only when BOTH messages state one)
# --------------------------------------------------------------------------- #
def test_runway_side_only_in_one_message_is_not_a_discrepancy():
    # Small extractors often invent a side; an unstated side is not an error.
    inst = fields(callsign="Air Europa 75", runway={"number": "06", "side": "left"})
    rb = fields(callsign="Air Europa 75", runway={"number": "06"})
    assert compare_fields(inst, rb) == []


def test_runway_side_differs_in_both_is_flagged():
    inst = fields(callsign="Air Europa 75", runway={"number": "32", "side": "left"})
    rb = fields(callsign="Air Europa 75", runway={"number": "32", "side": "right"})
    assert categories(inst, rb) == [VALUE_SUBSTITUTION]
    assert affected(inst, rb) == ["runway"]


def test_runway_number_error_still_detected_with_sides():
    inst = fields(callsign="Vueling 38 Lima", runway={"number": "24"})
    rb = fields(callsign="Vueling 38 Lima", runway={"number": "23"})
    assert categories(inst, rb) == [VALUE_SUBSTITUTION]


def test_runway_single_digit_zero_pad_matches():
    # "cleared to land runway zero six", the model may drop the pad on one side
    # ("6") and keep it on the other ("06"); same runway, so no discrepancy.
    inst = fields(callsign="Air Europa 75", runway={"number": "06"})
    rb = fields(callsign="Air Europa 75", runway={"number": "6"})
    assert compare_fields(inst, rb) == []


def test_runway_number_as_int_normalizes():
    # LLM JSON sometimes emits the runway number as an int despite the schema;
    # 6 must canonicalize to "06" so it matches a zero-padded clearance.
    inst = fields(callsign="Air Europa 75", runway={"number": "06"})
    rb = fields(callsign="Air Europa 75", runway={"number": 6})
    assert compare_fields(inst, rb) == []


# --------------------------------------------------------------------------- #
# omission
# --------------------------------------------------------------------------- #
def test_omission_heading():
    inst = fields(
        callsign="Speedbird 245",
        altitude={"kind": "FL", "value": 240},
        heading={"value": 270, "direction": "left"},
    )
    rb = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 240})
    assert categories(inst, rb) == [OMISSION]
    assert affected(inst, rb) == ["heading"]


def test_omission_multiple_acknowledgement_only():
    # "Wilco, Speedbird 245." -> nothing read back; both items omitted.
    inst = fields(
        callsign="Speedbird 245",
        altitude={"kind": "FL", "value": 200},
        heading={"value": 270, "direction": "left"},
    )
    rb = fields(callsign="Speedbird 245")
    cats = categories(inst, rb)
    assert cats == [OMISSION, OMISSION]
    assert set(affected(inst, rb)) == {"altitude", "heading"}


# --------------------------------------------------------------------------- #
# callsign_error
# --------------------------------------------------------------------------- #
def test_callsign_digit_error():
    inst = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 280})
    rb = fields(callsign="Speedbird 254", altitude={"kind": "FL", "value": 280})
    assert categories(inst, rb) == [CALLSIGN_ERROR]
    assert affected(inst, rb) == ["callsign"]


def test_callsign_missing():
    inst = fields(callsign="Easy 4471", squawk="4271")
    rb = fields(squawk="4271")
    assert categories(inst, rb) == [CALLSIGN_ERROR]


def test_callsign_similar_confusion():
    inst = fields(callsign="Ryanair 12 Quebec", frequency="118.7")
    rb = fields(callsign="Ryanair 12 Golf", frequency="118.7")
    assert categories(inst, rb) == [CALLSIGN_ERROR]


# --------------------------------------------------------------------------- #
# added_element
# --------------------------------------------------------------------------- #
def test_added_element_heading():
    inst = fields(callsign="Speedbird 245", altitude={"kind": "FL", "value": 240})
    rb = fields(
        callsign="Speedbird 245",
        altitude={"kind": "FL", "value": 240},
        heading={"value": 270, "direction": "left"},
    )
    assert categories(inst, rb) == [ADDED_ELEMENT]
    assert affected(inst, rb) == ["heading"]


def test_added_element_squawk():
    inst = fields(callsign="Easy 4471", frequency="118.7")
    rb = fields(callsign="Easy 4471", frequency="118.7", squawk="7000")
    assert categories(inst, rb) == [ADDED_ELEMENT]
    assert affected(inst, rb) == ["squawk"]
