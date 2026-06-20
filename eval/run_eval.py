"""Run the ATC Readback Verifier over the labelled test set and report metrics.

Usage:
    python eval/run_eval.py                       # uses EXTRACTOR_BACKEND from .env
    python eval/run_eval.py --backend ollama --model qwen2.5:3b
    python eval/run_eval.py --limit 10            # quick smoke test

Outputs (written to eval/results/):
    metrics.md / metrics.json   precision, recall, F1, false-alarm rate, confusion
    predictions.csv             per-case predicted vs expected (full audit trail)
    failures.md                 misclassified / mismatched cases for failure analysis
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make `src/` importable without installing the package (works on any machine).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from metrics import EvalRecord, compute_metrics, format_metrics_markdown  # noqa: E402

from atc_verifier import verify  # noqa: E402
from atc_verifier.extract.base import get_extractor  # noqa: E402

DATA = ROOT / "eval" / "data" / "atc_readback_test_set.csv"
RESULTS = ROOT / "eval" / "results"


def parse_gold_fields(affected: str) -> list[str]:
    """Turn the gold ``affected_field`` cell into a list the metrics understand."""
    value = (affected or "").strip().lower()
    if value in ("", "none"):
        return []
    if value == "multiple":
        return ["__multiple__"]
    return [part.strip() for part in value.split(";") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default=None, help="ollama | hf (default: env)")
    parser.add_argument("--model", default=None, help="model name override")
    parser.add_argument("--limit", type=int, default=None, help="only run first N cases")
    parser.add_argument("--data", default=str(DATA), help="path to the test-set CSV")
    parser.add_argument("--out", default=str(RESULTS), help="output directory for results")
    parser.add_argument(
        "--allow-errors",
        action="store_true",
        help="write results even if some cases failed to extract. By default the "
        "run aborts with a non-zero exit when any case errors, so a no-model run "
        "(e.g. Ollama down) cannot silently overwrite committed metrics with zeros.",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    results_dir = Path(args.out)

    extractor_kwargs = {"model": args.model} if args.model else {}
    extractor = get_extractor(args.backend, **extractor_kwargs)
    backend_name = extractor.name
    model_name = getattr(extractor, "model", "unknown")

    df = pd.read_csv(args.data)
    if args.limit:
        df = df.head(args.limit)

    print(f"Running {len(df)} cases  |  backend={backend_name}  model={model_name}\n")

    records: list[EvalRecord] = []
    rows_out: list[dict] = []
    for _, row in df.iterrows():
        rid = str(row["id"])
        try:
            result = verify(str(row["instruction"]), str(row["readback"]), extractor)
            inst_raw = result.instruction_fields.raw
            rb_raw = result.readback_fields.raw
            if not inst_raw and not rb_raw:
                # Both messages extracted to nothing: a silent extraction failure
                # (empty / unparseable output) that the comparator would otherwise
                # score as a confident MATCH, inflating the metrics. Treat it as an
                # error so the guard below catches it instead.
                raise RuntimeError("empty extraction (no fields parsed from either message)")
            pred_verdict = result.status
            pred_categories = result.verdict.categories
            pred_fields = result.verdict.affected_fields
        except Exception as exc:  # keep going; record the failure
            pred_verdict, pred_categories, pred_fields = "ERROR", [str(exc)], []
            inst_raw, rb_raw = {}, {}

        rec = EvalRecord(
            id=rid,
            gold_verdict=str(row["expected_verdict"]).strip(),
            pred_verdict=pred_verdict,
            gold_category=str(row["error_category"]).strip(),
            pred_categories=pred_categories,
            gold_fields=parse_gold_fields(str(row["affected_field"])),
            pred_fields=pred_fields,
        )
        records.append(rec)

        mark = "ok " if rec.verdict_correct else "XX "
        print(f"  {mark}{rid}: gold={rec.gold_verdict:<11} pred={pred_verdict}")

        rows_out.append(
            {
                "id": rid,
                "instruction": row["instruction"],
                "readback": row["readback"],
                "gold_verdict": rec.gold_verdict,
                "pred_verdict": pred_verdict,
                "gold_category": rec.gold_category,
                "pred_categories": "; ".join(pred_categories),
                "gold_fields": "; ".join(rec.gold_fields),
                "pred_fields": "; ".join(pred_fields),
                "verdict_correct": rec.verdict_correct,
                "category_correct": rec.category_correct,
                "instruction_extracted": json.dumps(inst_raw, ensure_ascii=False),
                "readback_extracted": json.dumps(rb_raw, ensure_ascii=False),
            }
        )

    # Guard: an extractor failure is recorded as an "ERROR" verdict that the
    # metrics silently drop from the confusion matrix, so a run where the
    # backend is unavailable would otherwise write all-zero metrics and still
    # exit 0, quietly overwriting the committed real results. Fail loudly.
    errored = [(rec, row) for rec, row in zip(records, rows_out) if rec.pred_verdict == "ERROR"]
    if errored and not args.allow_errors:
        print(
            f"\nERROR: {len(errored)}/{len(records)} case(s) failed to extract: "
            "the extractor backend looks unavailable (e.g. Ollama not running, "
            "the model not pulled, or no HF token)."
        )
        for rec, row in errored:
            print(f"  {rec.id}: {row['pred_categories']}")
        print(
            "\nRefusing to write metrics (zeros would overwrite the committed "
            "results). Fix the backend, or pass --allow-errors to force a write."
        )
        return 1

    metrics = compute_metrics(records)

    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "metrics.json").write_text(
        json.dumps(
            {"backend": backend_name, "model": model_name, "errors": len(errored), **metrics},
            indent=2,
        ),
        encoding="utf-8",
    )
    (results_dir / "metrics.md").write_text(
        format_metrics_markdown(metrics, backend=backend_name, model=model_name),
        encoding="utf-8",
    )
    pd.DataFrame(rows_out).to_csv(results_dir / "predictions.csv", index=False)
    _write_failures(rows_out, results_dir)

    m = metrics
    print(
        f"\nDone. P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} "
        f"false-alarm={m['false_alarm_rate']:.2f} acc={m['verdict_accuracy']:.2f}"
    )
    print(f"Wrote results to {results_dir}/")
    return 0


def _write_failures(rows_out: list[dict], results_dir: Path) -> None:
    failures = [r for r in rows_out if not r["verdict_correct"] or not r["category_correct"]]
    lines = [
        "# Failure cases",
        "",
        f"{len(failures)} case(s) where the verdict or the error category was wrong. "
        "Each shows the model's extracted fields so the cause can be diagnosed.",
        "",
    ]
    for r in failures:
        lines += [
            f"## {r['id']}",
            f"- **Instruction:** {r['instruction']}",
            f"- **Readback:** {r['readback']}",
            f"- **Gold:** {r['gold_verdict']} / {r['gold_category']} / "
            f"[{r['gold_fields']}]",
            f"- **Predicted:** {r['pred_verdict']} / {r['pred_categories']} / "
            f"[{r['pred_fields']}]",
            f"- **Extracted (instruction):** `{r['instruction_extracted']}`",
            f"- **Extracted (readback):** `{r['readback_extracted']}`",
            "- **Hypothesis:** _<fill in: extraction error? normalization gap? "
            "label ambiguity?>_",
            "",
        ]
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "failures.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
