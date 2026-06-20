# Evaluation results: ATC Readback Verifier

- **Backend:** `ollama`  |  **Model:** `qwen2.5:3b`
- **Test cases:** 50

## Error-detection metrics (positive class = readback contains an error)

| Metric | Value |
|---|---|
| Precision | 94.3% |
| Recall | 97.1% |
| F1 | 95.7% |
| False-alarm rate (on correct readbacks) | 12.5% |
| Verdict accuracy (MATCH vs DISCREPANCY) | 94.0% |
| Error-category accuracy | 91.2% |
| Affected-field accuracy | 90.0% |

## Confusion matrix

| | predicted MATCH | predicted DISCREPANCY |
|---|---|---|
| **gold MATCH** | 14 (TN) | 2 (FP, false alarm) |
| **gold DISCREPANCY** | 1 (FN, missed) | 33 (TP) |

## Detection recall by error category

| Category | N | Detected | Detection recall | Category accuracy |
|---|---|---|---|---|
| added_element | 3 | 2 | 66.7% | 66.7% |
| callsign_error | 5 | 5 | 100.0% | 100.0% |
| digit_transposition | 7 | 7 | 100.0% | 85.7% |
| omission | 8 | 8 | 100.0% | 87.5% |
| value_substitution | 11 | 11 | 100.0% | 100.0% |
