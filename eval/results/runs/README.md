# Archived evaluation runs

These per-run folders are **raw, auto-generated snapshots** of each evaluation
(`3b_baseline_v1`, `3b_improved_v2`, `3b_final_v3`, `7b_final_v3`), kept as an
audit trail. Each contains the `metrics.json` / `metrics.md`, `predictions.csv`,
and a `failures.md` exactly as emitted by `eval/run_eval.py`.

The `failures.md` files here are the unedited template output, so their
`**Hypothesis:**` lines are still the auto-generated `_<fill in: ...>_`
placeholder. The **analysed** failure write-up — with the actual hypotheses and
root-cause reasoning — lives in:

- `eval/results/failures.md` (top level, the final run), and
- `docs/report/failure_analysis.md` (the full narrative, Appendix B of the report).

The headline numbers in the report trace to `eval/results/metrics.json`
(identical to `runs/3b_final_v3/metrics.json`).
