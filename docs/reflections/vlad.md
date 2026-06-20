# Individual Reflection: Vlad

**Role:** Comparator core IP: the deterministic field-by-field comparator, the typed 8-field schema and normalization, the 5-category taxonomy, and the comparator unit tests (`src/atc_verifier/compare.py`, `verdict.py`, `schema.py`, `tests/test_compare.py`).

## My specific contributions

I built the deterministic half of the system: the LLM only extracts, and every MATCH-or-discrepancy judgement is my Python. I designed the typed schema in `schema.py`: the 8 fields (`callsign, altitude, heading, speed, frequency, squawk, runway, qnh`), with sub-structures for `Altitude` (FL vs ALT feet), `Heading`, and `Runway`, plus the normalization that makes semantically-equal readbacks compare equal: telephony "one zero one three" → 1013, `normalize_frequency` trimming 118.70 → 118.7, `normalize_squawk` preserving leading zeros via `zfill(4)`, and the policy that wind is informational and must never map to heading/speed. In `compare.py` I wrote `compare_fields` and the per-field rules, and I defined the 5-category taxonomy (`value_substitution, digit_transposition, omission, callsign_error, added_element`). I wrote the 26 unit tests in `tests/test_compare.py`, which run with no LLM.

## What I learned (NLP and engineering)

The biggest lesson: extraction is the bottleneck, not comparison. Across the whole iteration the comparator was *never* the cause of a failure, the one residual miss (TC12) was an extraction miss the model handed me, not a logic error. I also learned to separate failure *modes* that look similar: `_is_transposition` flags a digit reorder only when two values share the same digit multiset in a different order (squawk 5701 → 5071 is a transposition; FL240 → FL250 is a substitution), which matters because a transposition is a distinct, higher-risk readback error worth its own category.

## Challenges and how I handled them

The runway false alarms. Small models hallucinate an L/R/C side, so comparing a stated side against an invented one fired spurious discrepancies. My fix in `_compare_runway` was principled: compare the runway *number* first, and flag a side difference *only when both messages explicitly state a side*. That single rule killed the runway-side false alarms and was the comparator-side half of the final fix that brought the false-alarm rate down to 6.2%. Callsign I kept strict: `_compare_callsign` treats any mismatch as a `callsign_error` because it is the aircraft's identity, even if the digits happen to be a transposition.

## If I did it again

I'd add a confidence/abstain signal so that when extraction is shaky (the TC12 situation) the comparator can surface "uncertain" rather than silently trusting a partial field, and I'd grow `tests/test_compare.py` with property-based tests over normalization edge cases.

## Use of AI tools (personal note)

I used an AI assistant to draft docstrings and brainstorm edge cases for transposition detection, but I verified every rule myself by writing the 26 unit tests in `tests/test_compare.py` and stepping through real cases like TC07, TC12, and TC33 by hand against the gold labels. Where the assistant suggested over-clever logic, I rejected it in favour of code I could defend line-by-line in the Q&A.
