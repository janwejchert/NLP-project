"""Unit tests for the evaluation metrics (eval/metrics.py).

These pin the headline safety arithmetic — false-alarm rate, precision/recall/F1,
the confusion matrix, per-category detection recall, and the zero-denominator
guards — on small fixed record sets, independent of any model run.
"""

from __future__ import annotations

from metrics import DISCREPANCY, MATCH, EvalRecord, _safe_div, compute_metrics


def _rec(gold_v, pred_v, gold_c="correct", pred_c=None, gold_f=None, pred_f=None):
    return EvalRecord(
        id="T",
        gold_verdict=gold_v,
        pred_verdict=pred_v,
        gold_category=gold_c,
        pred_categories=pred_c or [],
        gold_fields=gold_f or [],
        pred_fields=pred_f or [],
    )


def test_safe_div():
    assert _safe_div(1, 0) == 0.0
    assert _safe_div(3, 4) == 0.75


def test_confusion_and_core_metrics():
    records = [
        _rec(DISCREPANCY, DISCREPANCY, "value_substitution", ["value_substitution"],
             ["altitude"], ["altitude"]),  # TP
        _rec(DISCREPANCY, MATCH, "omission", [], ["heading"], []),  # FN
        _rec(MATCH, DISCREPANCY, "correct", ["value_substitution"], [], ["speed"]),  # FP
        _rec(MATCH, MATCH),  # TN
    ]
    m = compute_metrics(records)
    assert m["confusion"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert m["precision"] == 0.5
    assert m["recall"] == 0.5
    assert m["f1"] == 0.5
    assert m["false_alarm_rate"] == 0.5  # fp / (fp + tn)
    assert m["verdict_accuracy"] == 0.5  # (tp + tn) / total


def test_false_alarm_rate_zero_without_false_positives():
    records = [
        _rec(MATCH, MATCH),
        _rec(MATCH, MATCH),
        _rec(DISCREPANCY, DISCREPANCY, "omission", ["omission"], ["heading"], ["heading"]),
    ]
    assert compute_metrics(records)["false_alarm_rate"] == 0.0


def test_empty_records_all_zero():
    m = compute_metrics([])
    assert m["precision"] == 0.0
    assert m["recall"] == 0.0
    assert m["f1"] == 0.0
    assert m["false_alarm_rate"] == 0.0
    assert m["verdict_accuracy"] == 0.0


def test_per_category_detection_recall():
    records = [
        _rec(DISCREPANCY, DISCREPANCY, "omission", ["omission"], ["heading"], ["heading"]),
        _rec(DISCREPANCY, MATCH, "omission", [], ["speed"], []),  # missed
    ]
    bucket = compute_metrics(records)["per_category"]["omission"]
    assert bucket["n"] == 2
    assert bucket["detected"] == 1
    assert bucket["detection_recall"] == 0.5


def test_eval_record_properties():
    assert _rec(MATCH, MATCH).verdict_correct
    assert _rec(MATCH, MATCH).category_correct  # trivially true for correct readbacks
    multi = _rec(DISCREPANCY, DISCREPANCY, "omission", ["omission"], ["__multiple__"], ["a", "b"])
    assert multi.fields_correct  # "__multiple__" gold => >=2 predicted fields
    wrong_cat = _rec(DISCREPANCY, DISCREPANCY, "value_substitution", ["omission"],
                     ["altitude"], ["altitude"])
    assert not wrong_cat.category_correct  # gold category not among predicted
