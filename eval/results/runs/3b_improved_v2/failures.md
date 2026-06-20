# Failure cases

7 case(s) where the verdict or the error category was wrong. Each shows the model's extracted fields so the cause can be diagnosed.

## TC08
- **Instruction:** Air Europa 75, line up and wait runway 06.
- **Readback:** Line up and wait runway 06, Air Europa 75.
- **Gold:** MATCH / correct / []
- **Predicted:** DISCREPANCY / value_substitution / [runway]
- **Extracted (instruction):** `{"callsign": "Air Europa 75", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "06", "side": "left"}, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Air Europa 75", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "06", "side": null}, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC11
- **Instruction:** G-ABCD, after the landing Cessna, line up and wait runway 18.
- **Readback:** Line up and wait runway 18 after the landing Cessna, G-ABCD.
- **Gold:** MATCH / correct / []
- **Predicted:** DISCREPANCY / value_substitution / [runway]
- **Extracted (instruction):** `{"callsign": "G-ABCD", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "18", "side": null}, "qnh": null}`
- **Extracted (readback):** `{"callsign": "G-ABCD", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "18", "side": "left"}, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC12
- **Instruction:** Easy 4471, reduce speed 210 knots, descend flight level 100.
- **Readback:** Speed 210 knots, descend flight level 100, Easy 4471.
- **Gold:** MATCH / correct / []
- **Predicted:** DISCREPANCY / value_substitution / [squawk]
- **Extracted (instruction):** `{"callsign": "Easy 4471", "altitude": {"kind": "FL", "value": 100}, "heading": null, "speed": 210, "frequency": null, "squawk": "0421", "runway": null, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Easy 4471", "altitude": {"kind": "FL", "value": 100}, "heading": null, "speed": 210, "frequency": null, "squawk": "4471", "runway": null, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC13
- **Instruction:** Speedbird 245, cleared ILS approach runway 24.
- **Readback:** Cleared ILS approach runway 24, Speedbird 245.
- **Gold:** MATCH / correct / []
- **Predicted:** DISCREPANCY / added_element / [heading]
- **Extracted (instruction):** `{"callsign": "Speedbird 245", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "24", "side": "left"}, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Speedbird 245", "altitude": null, "heading": {"value": 240, "direction": "right"}, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "24", "side": "left"}, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC37
- **Instruction:** Easy 4471, descend altitude 4000 feet, squawk 4271.
- **Readback:** Descend altitude 4000 feet, Easy 4471.
- **Gold:** DISCREPANCY / omission / [squawk]
- **Predicted:** DISCREPANCY / value_substitution / [squawk]
- **Extracted (instruction):** `{"callsign": "Easy 4471", "altitude": {"kind": "ALT", "value": 4000}, "heading": null, "speed": null, "frequency": null, "squawk": "4271", "runway": null, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Easy 4471", "altitude": {"kind": "ALT", "value": 4000}, "heading": null, "speed": null, "frequency": null, "squawk": "4471", "runway": null, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC39
- **Instruction:** Vueling 38 Lima, cleared to land runway 24.
- **Readback:** Cleared to land, Vueling 38 Lima.
- **Gold:** DISCREPANCY / omission / [runway]
- **Predicted:** DISCREPANCY / value_substitution / [runway]
- **Extracted (instruction):** `{"callsign": "Vueling 38 Lima", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "24", "side": null}, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Vueling 38 Lima", "altitude": null, "heading": null, "speed": null, "frequency": null, "squawk": null, "runway": {"number": "24", "side": "left"}, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_

## TC50
- **Instruction:** Easy 4471, contact Tower 118.7.
- **Readback:** Tower 118.7, squawk 7000, Easy 4471.
- **Gold:** DISCREPANCY / added_element / [squawk]
- **Predicted:** DISCREPANCY / value_substitution / [squawk]
- **Extracted (instruction):** `{"callsign": "Easy 4471", "altitude": null, "heading": null, "speed": null, "frequency": "118.7", "squawk": "4471", "runway": null, "qnh": null}`
- **Extracted (readback):** `{"callsign": "Easy 4471", "altitude": null, "heading": null, "speed": null, "frequency": "118.7", "squawk": "7000", "runway": null, "qnh": null}`
- **Hypothesis:** _<fill in: extraction error? normalization gap? label ambiguity?>_
