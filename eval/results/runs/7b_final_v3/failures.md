# Failure cases

1 case(s) where the verdict or the error category was wrong. Each shows the model's extracted fields so the cause can be diagnosed.

## TC20
- **Instruction:** Ryanair 12 Quebec, contact Tower 118.7.
- **Readback:** Tower 118.9, Ryanair 12 Quebec.
- **Gold:** DISCREPANCY / value_substitution / [frequency]
- **Predicted:** DISCREPANCY / omission / [frequency]
- **Extracted (instruction):** `{"callsign": "Ryanair 12 Quebec", "altitude": null, "heading": null, "speed": null, "frequency": "118.7", "squawk": null, "runway": null, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Ryanair 12 Quebec", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": null, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_
