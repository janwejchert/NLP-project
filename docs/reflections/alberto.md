# Individual Reflection — Alberto

**Role:** Evaluation & metrics — owner of the evaluation harness (`eval/run_eval.py`), the metric definitions (`eval/metrics.py`), and the reproducible runs in `eval/results/`.

## My specific contributions

I built the harness that turns our 50-case labelled set into numbers. The central design decision was framing the **positive class as "the readback contains an error"** (see the module docstring and `compute_metrics` in `eval/metrics.py`), so precision, recall and F1 measure *error detection*, not generic accuracy. On top of the standard 2×2 confusion matrix I added the metric I care about most: the **false-alarm rate** in `compute_metrics` — `fp / (fp + tn)`, the fraction of genuinely-correct readbacks we wrongly flag. I also added **per-category detection recall** so we can prove we catch every one of the five taxonomy categories (value_substitution, digit_transposition, omission, callsign_error, added_element), and the `EvalRecord` properties `category_correct` / `fields_correct` for lenient category and affected-field scoring. In `run_eval.py` I made runs reproducible (temperature 0, pinned model tag, a `--out` flag so each run archives under `eval/results/runs/`) and wrote `predictions.csv` carrying the model's raw extracted JSON for both messages, plus an auto-generated `failures.md`. I produced the baseline, hardened, final and 7b runs that quantified the iteration: a +12.5pp false-alarm regression on hardening (12.5% → 25.0%), then a **−18.8pp recovery (25.0% → 6.2%)** from the principled final fix.

## What I learned (NLP and engineering)

The biggest lesson was making "the prompt feels better" *measurable*. Our "hardening" attempt subjectively read like an improvement, but my harness showed it regressed false-alarm from 12.5% to 25%. Without a committed metric and the raw-JSON audit trail, that regression ships silently. I also learned why in a safety setting false-alarm rate dominates raw accuracy: a verifier that cries wolf gets switched off, so a 6.2% false-alarm rate is a *headline*, not a footnote.

## Challenges and how I handled them

Diagnosing failures was hard until I logged each model's extracted fields per case. That turned TC12 from "a wrong verdict" into a visible **extraction miss**, and proved the comparator was never the cause — every residual error lived upstream in extraction. I also had to keep the harness backend-agnostic so the same code scored both ollama (3b) and hf (7b) runs.

## If I did it again

I'd add confidence intervals or bootstrap resampling — 50 cases is thin, and one flipped case (TC12) moves F1 noticeably. I'd also script the run-comparison diff instead of eyeballing two `metrics.md` files.

## Use of AI tools (personal note)

I used an AI assistant to sketch the per-category aggregation loop and the markdown formatter in `eval/metrics.py`, then verified every formula by hand against the confusion counts (TP 34, FP 1, FN 0, TN 15) and re-derived F1 = 0.986 myself before trusting it. I treated generated code as a draft to audit, never as ground truth.
