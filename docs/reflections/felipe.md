# Individual Reflection: Felipe

**Role:** Extraction & prompts, owner of `src/atc_verifier/extract/` (the `Extractor` interface and factory, both backends, and the few-shot prompt `prompts/extract_fields.txt`).

## My specific contributions

I built the extraction layer that turns one radio message into our 8-field schema. In `base.py` I wrote the abstract `Extractor` interface and the `get_extractor` factory, which reads `EXTRACTOR_BACKEND` and lazily imports either `OllamaExtractor` (local qwen2.5:3b, temperature 0 for determinism) or `HuggingFaceExtractor` (Qwen2.5-7B-Instruct, for Jan's hosted demo) so the app never needs both dependency sets. I wrote the shared `parse_model_json` helper: it strips code fences, grabs the first balanced `{...}` block, and returns `{}` rather than crashing, plus the one stricter "Return ONLY the JSON object" retry in `extract()`. Centralising cleanup here means both backends behave identically. I also authored and iterated the few-shot prompt itself.

## What I learned (NLP and engineering)

The big lesson was that prompt engineering for a small model is not "add more examples." During a hardening pass I added more few-shot cases and the false-alarm rate doubled to 25%, the 3b model started reading the `Easy 4471` callsign suffix as a squawk and `runway 24` as `heading 240`. The extra examples poisoned it. The fix that stuck was safe *rules*, not examples: squawk comes only from an explicit `squawk` instruction (never callsign digits), never guess a runway side, and wind ("wind 250 degrees 8 knots") is informational, never a heading or speed. I learned that with small models, constraints generalise where examples overfit.

## Challenges and how I handled them

Extraction is the bottleneck: every residual failure was a missed field, never a comparator bug. TC12 still fails on 3b as a pure extraction miss, and 7B reads it correctly. I leaned on temperature 0 and `parse_model_json` so non-determinism and malformed JSON never contaminated Alberto's eval runs.

## If I did it again

I'd add a tiny per-field regression harness for extraction alone (e.g. asserting `Easy 4471` keeps `squawk: null`), so prompt edits get caught before they reach the comparator. I'd also try a constrained-decoding / JSON-schema mode to retire the brace-matching fallback.

## Use of AI tools (personal note)

I used an AI assistant to draft candidate prompt rules and brainstorm failure hypotheses for the poisoning regression, but I verified every change by re-running extraction on the offending cases (TC07, TC12, TC33) and reading the raw JSON myself before trusting any false-alarm number.
