# Evaluation results: ATC Readback Verifier

- **Backend:** `ollama`  |  **Model:** `qwen2.5:3b`
- **Test cases:** 50

## Error-detection metrics (positive class = readback contains an error)

| Metric | Value |
|---|---|
| Precision | 97.1% |
| Recall | 100.0% |
| F1 | 98.6% |
| False-alarm rate (on correct readbacks) | 6.2% |
| Verdict accuracy (MATCH vs DISCREPANCY) | 98.0% |
| Error-category accuracy | 100.0% |
| Affected-field accuracy | 90.0% |

## Confusion matrix

| | predicted MATCH | predicted DISCREPANCY |
|---|---|---|
| **gold MATCH** | 15 (TN) | 1 (FP, false alarm) |
| **gold DISCREPANCY** | 0 (FN, missed) | 34 (TP) |

## Detection recall by error category

| Category | N | Detected | Detection recall | Category accuracy |
|---|---|---|---|---|
| added_element | 3 | 3 | 100.0% | 100.0% |
| callsign_error | 5 | 5 | 100.0% | 100.0% |
| digit_transposition | 7 | 7 | 100.0% | 100.0% |
| omission | 8 | 8 | 100.0% | 100.0% |
| value_substitution | 11 | 11 | 100.0% | 100.0% |
