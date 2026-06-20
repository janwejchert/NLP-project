# Failure cases

5 case(s) where the verdict or the error category was wrong. Each shows the model's extracted fields so the cause can be diagnosed.

## TC07
- **Instruction:** Vueling 38 Lima, cleared to land runway 24, wind 250 degrees 8 knots.
- **Readback:** Cleared to land runway 24, Vueling 38 Lima.
- **Gold:** MATCH / correct / []
- **Predicted:** DISCREPANCY / omission; value_substitution / [heading; speed; runway]
- **Extracted (instruction):** `{"callsign": "Vueling 38 Lima", "altitude": null, "heading": {"value": 250, "direction": "right"}, "speed": 8, "frequency": null, "squawk": null, "runway": {"number": "24", "side": "right"}, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Vueling 38 Lima", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "24", "side": "left"}, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC11
- **Instruction:** G-ABCD, after the landing Cessna, line up and wait runway 18.
- **Readback:** Line up and wait runway 18 after the landing Cessna, G-ABCD.
- **Gold:** MATCH / correct / []
- **Predicted:** DISCREPANCY / value_substitution / [runway]
- **Extracted (instruction):** `{"callsign": "G-ABCD", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "18", "side": "left"}, "qnh": null}`
- **Extracted (readback):** `{"callsign": "G-ABCD", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "18", "side": "right"}, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC28
- **Instruction:** Easy 4471, squawk 5701.
- **Readback:** Squawk 5071, Easy 4471.
- **Gold:** DISCREPANCY / digit_transposition / [squawk]
- **Predicted:** DISCREPANCY / value_substitution / [squawk]
- **Extracted (instruction):** `{"callsign": "Easy 4471", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": "5701", "runway": null, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Easy 4471", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": "0507", "runway": null, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC39
- **Instruction:** Vueling 38 Lima, cleared to land runway 24.
- **Readback:** Cleared to land, Vueling 38 Lima.
- **Gold:** DISCREPANCY / omission / [runway]
- **Predicted:** DISCREPANCY / value_substitution / [runway]
- **Extracted (instruction):** `{"callsign": "Vueling 38 Lima", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "24", "side": "left"}, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Vueling 38 Lima", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "24", "side": "right"}, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC49
- **Instruction:** Iberia 6020, turn right heading 120.
- **Readback:** Right heading 120, descending flight level 100, Iberia 6020.
- **Gold:** DISCREPANCY / added_element / [altitude]
- **Predicted:** MATCH /  / []
- **Extracted (instruction):** `{"callsign": "Iberia 6020", "altitude": null, "heading": {"value": 120, "direction": "right"}, "speed": null, "frequency": null, "squawk": null, "runway": null, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Iberia 6020", "altitude": null, "heading": {"value": 120, "direction": "right"}, "speed": null, "frequency": null, "squawk": null, "runway": null, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_
