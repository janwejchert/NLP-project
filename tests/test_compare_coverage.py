"""Additional comparator coverage, added during a review pass.

Complements ``tests/test_compare.py`` by closing coverage gaps it did not reach:
the ``speed`` field (untested in every branch), qnh transposition, the FL-vs-feet
distinction, leading-zero squawk transposition, a combined runway number+side
mismatch (and its rendered detail string), the empty-callsign branch, and the
schema robustness fixes for whitespace/packed-side runways and decimal ints.
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


def f(**kw):
    return ExtractedFields.from_json(kw)


def cats(a, b):
    return [d.category for d in compare_fields(a, b)]


# --------------------------------------------------------------------------- #
# speed: every branch of the generic comparator path
# --------------------------------------------------------------------------- #
def test_speed_value_substitution():
    assert cats(f(speed=250), f(speed=280)) == [VALUE_SUBSTITUTION]


def test_speed_digit_transposition():
    assert cats(f(speed=250), f(speed=520)) == [DIGIT_TRANSPOSITION]


def test_speed_omission():
    assert cats(f(speed=250), f()) == [OMISSION]


def test_speed_added_element():
    assert cats(f(), f(speed=250)) == [ADDED_ELEMENT]


def test_speed_match():
    assert compare_fields(f(speed=250), f(speed=250)) == []


# --------------------------------------------------------------------------- #
# qnh transposition and the FL-vs-feet distinction
# --------------------------------------------------------------------------- #
def test_qnh_transposition():
    assert cats(f(qnh=1013), f(qnh=1031)) == [DIGIT_TRANSPOSITION]


def test_flight_level_vs_feet_same_number_is_substitution():
    inst = f(altitude={"kind": "FL", "value": 240})
    rb = f(altitude={"kind": "ALT", "value": 240})
    assert cats(inst, rb) == [VALUE_SUBSTITUTION]


# --------------------------------------------------------------------------- #
# squawk leading-zero edge: documents the current zfill-vs-multiset behaviour
# --------------------------------------------------------------------------- #
def test_squawk_leading_zero_shuffle_is_transposition():
    assert cats(f(squawk="0700"), f(squawk="7000")) == [DIGIT_TRANSPOSITION]


# --------------------------------------------------------------------------- #
# runway: combined number+side mismatch and the rendered detail string
# --------------------------------------------------------------------------- #
def test_runway_number_and_side_both_differ_single_discrepancy():
    inst = f(runway={"number": "24", "side": "left"})
    rb = f(runway={"number": "23", "side": "right"})
    discs = compare_fields(inst, rb)
    assert [d.category for d in discs] == [VALUE_SUBSTITUTION]
    # No duplicated noun ("runway runway 24 ...").
    assert discs[0].detail == "instructed runway 24 left, read back as runway 23 right"


def test_runway_side_packed_in_number_token_is_detected():
    # "06L"/"06R" pack the side into the number token; the L/R must not be lost.
    assert cats(f(runway={"number": "06L"}), f(runway={"number": "06R"})) == [VALUE_SUBSTITUTION]


def test_whitespace_only_runway_number_is_absent():
    assert ExtractedFields.from_json({"runway": {"number": "  "}}).runway is None


# --------------------------------------------------------------------------- #
# callsign: empty-after-normalize, and omission
# --------------------------------------------------------------------------- #
def test_callsign_all_punctuation_normalizes_to_none():
    assert ExtractedFields.from_json({"callsign": "--- "}).callsign is None


def test_callsign_omission_is_callsign_error():
    assert cats(f(callsign="BAW245"), f()) == [CALLSIGN_ERROR]


# --------------------------------------------------------------------------- #
# _int tolerates decimal slop instead of concatenating bare digits
# --------------------------------------------------------------------------- #
def test_int_parses_decimal_value_by_rounding():
    assert ExtractedFields.from_json({"speed": "250.4"}).speed == 250
    assert ExtractedFields.from_json({"speed": "250.6"}).speed == 251


def test_heading_detail_string_has_no_duplicated_noun():
    inst = f(heading={"value": 270, "direction": "left"})
    rb = f(heading={"value": 250, "direction": "left"})
    discs = compare_fields(inst, rb)
    assert discs[0].detail == "instructed left heading 270, read back as left heading 250"


# --------------------------------------------------------------------------- #
# heading turn-direction: same "stated in both" rule as runway side
# --------------------------------------------------------------------------- #
def test_heading_direction_only_in_one_message_is_not_a_discrepancy():
    # An unstated turn direction is not a read-back error (mirrors runway side).
    assert compare_fields(f(heading={"value": 270, "direction": "left"}),
                          f(heading={"value": 270})) == []
    assert compare_fields(f(heading={"value": 270}),
                          f(heading={"value": 270, "direction": "left"})) == []


def test_heading_direction_differs_in_both_is_substitution():
    inst = f(heading={"value": 270, "direction": "left"})
    rb = f(heading={"value": 270, "direction": "right"})
    assert cats(inst, rb) == [VALUE_SUBSTITUTION]
