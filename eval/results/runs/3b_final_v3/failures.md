# Failure cases

1 case(s) where the verdict or the error category was wrong. Each shows the model's extracted fields so the cause can be diagnosed.

## TC12
- **Instruction:** Easy 4471, reduce speed 210 knots, descend flight level 100.
- **Readback:** Speed 210 knots, descend flight level 100, Easy 4471.
- **Gold:** MATCH / correct / []
- **Predicted:** DISCREPANCY / added_element / [altitude]
- **Extracted (instruction):** `{"callsign": "Easy 4471", "altitude": null, "heading": null, "speed": 210, "frequency": null, "squawk": null, "runway": null, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Easy 4471", "altitude": {"kind": "FL", "value": 100}, "heading": null, "speed": 210, "frequency": null, "squawk": null, "runway": null, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_
