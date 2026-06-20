# ATC Readback Verifier — extraction

The extraction component of the ATC Readback Verifier. It turns a single radio
message (a controller instruction or a pilot readback) into a structured set of
clearance fields so the instruction and the readback can be compared field by
field.

## What it extracts

Each message is reduced to eight fields, with `null` for anything not present:
`callsign`, `altitude`, `heading`, `speed`, `frequency`, `squawk`, `runway`,
and `qnh`. The exact schema and rules live in
[`src/atc_verifier/extract/prompts/extract_fields.txt`](src/atc_verifier/extract/prompts/extract_fields.txt).

## Layout

```
src/atc_verifier/extract/
  base.py            Extractor interface, backend factory, shared JSON parsing
  ollama_backend.py  local models via Ollama
  hf_backend.py      models via Hugging Face
  prompts/extract_fields.txt
tests/test_extract.py
docs/reflections/
```

## Usage

```python
from atc_verifier.extract import get_extractor

extractor = get_extractor()  # backend from EXTRACTOR_BACKEND, defaults to "ollama"
fields = extractor.extract("Speedbird 245, climb flight level 280.")
```

`get_extractor("hf")` selects the Hugging Face backend instead. Both backends
share the same prompt, JSON cleanup, and field normalization, so they behave
identically.

## Tests

```bash
pytest tests/test_extract.py
```
