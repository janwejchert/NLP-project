"""Unit tests for the model-output JSON parsing and the extractor factory.

``parse_model_json`` is the most failure-prone glue in the pipeline: small
instruction models wrap their JSON in prose or code fences. These tests pin its
branches (fences, embedded objects, brace-in-string, non-dict, garbage) with no
model in the loop, plus the ``get_extractor`` backend factory.
"""

from __future__ import annotations

import pytest

from atc_verifier.extract.base import get_extractor, parse_model_json


def test_plain_object():
    assert parse_model_json('{"callsign": "BAW245"}') == {"callsign": "BAW245"}


def test_fenced_json():
    assert parse_model_json('```json\n{"speed": 250}\n```') == {"speed": 250}


def test_object_embedded_in_prose():
    assert parse_model_json("Sure! Here it is:\n{\"qnh\": 1013}\nDone.") == {"qnh": 1013}


def test_non_json_brace_block_before_real_object_does_not_abort_search():
    # A "{field: value}" schema hint in the prose must not stop us finding the
    # real object later in the response.
    assert parse_model_json('e.g. {field: value}. {"callsign": "AB"}') == {"callsign": "AB"}


def test_brace_inside_string_value_is_respected():
    # The fallback scanner must treat a "}" inside a JSON string as data, not
    # structure (fast path is skipped here by the leading prose).
    assert parse_model_json('result: {"callsign": "a}b", "speed": 250}') == {
        "callsign": "a}b",
        "speed": 250,
    }


def test_top_level_array_recovers_embedded_object():
    assert parse_model_json('[{"callsign": "X"}]') == {"callsign": "X"}


def test_scalar_returns_empty_dict():
    assert parse_model_json('"none"') == {}
    assert parse_model_json("42") == {}


def test_empty_and_garbage_return_empty_dict():
    assert parse_model_json("") == {}
    assert parse_model_json("no json here at all") == {}


def test_get_extractor_unknown_backend_raises():
    with pytest.raises(ValueError):
        get_extractor("not-a-backend")
