"""Metrics for the ATC Readback Verifier evaluation.

Framing: a readback with at least one discrepancy is the *positive* class
("error present"). So:

* precision / recall / F1 measure how well we **detect** erroneous readbacks;
* the **false-alarm rate** is the fraction of genuinely-correct readbacks we
  wrongly flag, the metric that matters most in a safety setting, where crying
  wolf erodes trust.

We also report a 2x2 confusion matrix, per-error-category detection recall, and
how often the predicted error *category* and *affected field* match the gold
label.
"""

from __future__ import annotations

from dataclasses import dataclass

DISCREPANCY = "DISCREPANCY"
MATCH = "MATCH"


@dataclass
class EvalRecord:
    """One scored test case."""

    id: str
    gold_verdict: str
    pred_verdict: str
    gold_category: str  # e.g. "correct", "value_substitution"
    pred_categories: list[str]
    gold_fields: list[str]  # [] for none; ["__multiple__"] when gold says "multiple"
    pred_fields: list[str]

    @property
    def verdict_correct(self) -> bool:
        return self.gold_verdict == self.pred_verdict

    @property
    def category_correct(self) -> bool:
        """Did we surface the gold error category? (trivially true for correct)."""
        if self.gold_category == "correct":
            return self.pred_verdict == MATCH
        return self.gold_category in self.pred_categories

    @property
    def fields_correct(self) -> bool:
        """Did the predicted affected fields match the gold ones? (lenient)."""
        if self.gold_fields == ["__multiple__"]:
            return len(self.pred_fields) >= 2
        return set(self.gold_fields) == set(self.pred_fields)


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def compute_metrics(records: list[EvalRecord]) -> dict:
    tp = sum(r.gold_verdict == DISCREPANCY and r.pred_verdict == DISCREPANCY for r in records)
    fp = sum(r.gold_verdict == MATCH and r.pred_verdict == DISCREPANCY for r in records)
    fn = sum(r.gold_verdict == DISCREPANCY and r.pred_verdict == MATCH for r in records)
    tn = sum(r.gold_verdict == MATCH and r.pred_verdict == MATCH for r in records)
    total = len(records)

    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    false_alarm_rate = _safe_div(fp, fp + tn)
    accuracy = _safe_div(tp + tn, total)

    # Per-category detection recall (excluding "correct").
    per_category: dict[str, dict] = {}
    for r in records:
        if r.gold_category == "correct":
            continue
        bucket = per_category.setdefault(
            r.gold_category, {"n": 0, "detected": 0, "category_hit": 0}
        )
        bucket["n"] += 1
        bucket["detected"] += int(r.pred_verdict == DISCREPANCY)
        bucket["category_hit"] += int(r.category_correct)
    for b in per_category.values():
        b["detection_recall"] = _safe_div(b["detected"], b["n"])
        b["category_accuracy"] = _safe_div(b["category_hit"], b["n"])

    # Error-category accuracy is measured over the gold-DISCREPANCY cases only
    # (mirroring per_category, which excludes "correct"). Averaging over all
    # records would fold in the MATCH cases, where category_correct merely
    # re-tests the verdict, conflating this with verdict accuracy.
    error_records = [r for r in records if r.gold_category != "correct"]
    return {
        "n": total,
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "verdict_accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alarm_rate": false_alarm_rate,
        "category_accuracy": _safe_div(
            sum(r.category_correct for r in error_records), len(error_records)
        ),
        "field_accuracy": _safe_div(sum(r.fields_correct for r in records), total),
        "per_category": per_category,
    }


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def format_metrics_markdown(metrics: dict, *, backend: str, model: str) -> str:
    c = metrics["confusion"]
    lines = [
        "# Evaluation results: ATC Readback Verifier",
        "",
        f"- **Backend:** `{backend}`  |  **Model:** `{model}`",
        f"- **Test cases:** {metrics['n']}",
        "",
        "## Error-detection metrics (positive class = readback contains an error)",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Precision | {_pct(metrics['precision'])} |",
        f"| Recall | {_pct(metrics['recall'])} |",
        f"| F1 | {_pct(metrics['f1'])} |",
        f"| False-alarm rate (on correct readbacks) | {_pct(metrics['false_alarm_rate'])} |",
        f"| Verdict accuracy (MATCH vs DISCREPANCY) | {_pct(metrics['verdict_accuracy'])} |",
        f"| Error-category accuracy | {_pct(metrics['category_accuracy'])} |",
        f"| Affected-field accuracy | {_pct(metrics['field_accuracy'])} |",
        "",
        "## Confusion matrix",
        "",
        "| | predicted MATCH | predicted DISCREPANCY |",
        "|---|---|---|",
        f"| **gold MATCH** | {c['tn']} (TN) | {c['fp']} (FP, false alarm) |",
        f"| **gold DISCREPANCY** | {c['fn']} (FN, missed) | {c['tp']} (TP) |",
        "",
        "## Detection recall by error category",
        "",
        "| Category | N | Detected | Detection recall | Category accuracy |",
        "|---|---|---|---|---|",
    ]
    for name, b in sorted(metrics["per_category"].items()):
        lines.append(
            f"| {name} | {b['n']} | {b['detected']} | "
            f"{_pct(b['detection_recall'])} | {_pct(b['category_accuracy'])} |"
        )
    lines.append("")
    return "\n".join(lines)
