# Evaluation results — ATC Readback Verifier

- **Backend:** `ollama`  |  **Model:** `qwen2.5:7b`
- **Test cases:** 50

## Error-detection metrics (positive class = readback contains an error)

| Metric | Value |
|---|---|
| Precision | 100.0% |
| Recall | 100.0% |
| F1 | 100.0% |
| False-alarm rate (on correct readbacks) | 0.0% |
| Verdict accuracy (MATCH vs DISCREPANCY) | 100.0% |
| Error-category accuracy | 97.1% |
| Affected-field accuracy | 100.0% |

## Confusion matrix

| | predicted MATCH | predicted DISCREPANCY |
|---|---|---|
| **gold MATCH** | 16 (TN) | 0 (FP, false alarm) |
| **gold DISCREPANCY** | 0 (FN, missed) | 34 (TP) |

## Detection recall by error category

| Category | N | Detected | Detection recall | Category accuracy |
|---|---|---|---|---|
| added_element | 3 | 3 | 100.0% | 100.0% |
| callsign_error | 5 | 5 | 100.0% | 100.0% |
| digit_transposition | 7 | 7 | 100.0% | 100.0% |
| omission | 8 | 8 | 100.0% | 100.0% |
| value_substitution | 11 | 11 | 100.0% | 90.9% |
