# Evaluation results — ATC Readback Verifier

- **Backend:** `ollama`  |  **Model:** `qwen2.5:3b`
- **Test cases:** 50

## Error-detection metrics (positive class = readback contains an error)

| Metric | Value |
|---|---|
| Precision | 89.5% |
| Recall | 100.0% |
| F1 | 94.4% |
| False-alarm rate (on correct readbacks) | 25.0% |
| Verdict accuracy (MATCH vs DISCREPANCY) | 92.0% |
| Error-category accuracy | 91.2% |
| Affected-field accuracy | 86.0% |

## Confusion matrix

| | predicted MATCH | predicted DISCREPANCY |
|---|---|---|
| **gold MATCH** | 12 (TN) | 4 (FP, false alarm) |
| **gold DISCREPANCY** | 0 (FN, missed) | 34 (TP) |

## Detection recall by error category

| Category | N | Detected | Detection recall | Category accuracy |
|---|---|---|---|---|
| added_element | 3 | 3 | 100.0% | 66.7% |
| callsign_error | 5 | 5 | 100.0% | 100.0% |
| digit_transposition | 7 | 7 | 100.0% | 100.0% |
| omission | 8 | 8 | 100.0% | 75.0% |
| value_substitution | 11 | 11 | 100.0% | 100.0% |
