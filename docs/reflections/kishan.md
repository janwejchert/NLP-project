# Individual Reflection — Kishan

**Role:** Test set & data quality — owner of the 50-case labelled evaluation set (`eval/data/atc_readback_test_set.csv`).

## My specific contributions

I built and curated the entire 50-case labelled test set, `atc_readback_test_set.csv` (TC01–TC50), with its eight columns: `id`, `instruction`, `readback`, `expected_verdict`, `error_category`, `affected_field`, `expected_detail`, and `design_note`. I deliberately balanced it at 16 gold MATCH and 34 gold DISCREPANCY so the metrics could not be gamed by a model that simply always cries "discrepancy." I made sure all five error categories were covered with real spread: value_substitution (TC17–TC27), digit_transposition (TC28–TC34), omission (TC35–TC42), callsign_error (TC43–TC47), and added_element (TC48–TC50). I also seeded the hard cases that earned their keep: TC07 (wind is informational, must stay MATCH), TC10 (spelled-out "one zero one three"), TC11 (conditional clearance behind landing traffic), TC33 (runway 21→12, a high-risk transposition reversal), TC41 ("Wilco" — omission of every mandatory item), and TC47 ("12 Quebec" misheard as "12 Golf"). I owned the gold labels themselves and selected the failure cases for the failure-mode analysis.

## What I learned (NLP and engineering)

The deepest lesson was that **a label is an argument, not a fact.** Deciding TC07 should be MATCH meant I had to commit, in writing, to which items are *mandatory* readback items versus informational — wind isn't read back, so penalizing its absence would be wrong. That single choice shaped what "correct" even means downstream. I also learned how a small dataset exposes the real bottleneck: TC12, a plain two-item MATCH, is the one residual failure at 3b, and it's an *extraction* miss, never a comparator one — proof that data quality and extraction, not the deterministic logic, set the ceiling.

## Challenges and how I handled them

Designing two-error cases like TC27 (altitude *and* heading both wrong) without making the `affected_field` label ambiguous was hard; I used a semicolon convention (`altitude; heading`) so the gold stayed machine-checkable. Adversarial cases like TC33 and TC47 were the riskiest to label, because a sloppy gold would have masked exactly the safety-critical errors we most wanted to catch.

## If I did it again

I'd expand beyond 50 cases with more spelled-out-number and accent-style variants, and add near-miss MATCH cases (paraphrased but correct) to stress the false-alarm rate harder than TC10 and TC14 alone do.

## Use of AI tools (personal note)

I used an AI assistant to brainstorm candidate phrasings and to sanity-check my category definitions against ICAO readback conventions, but I hand-wrote and hand-verified every gold label myself, cross-reading each instruction/readback pair. Where the assistant proposed a "MATCH," I re-derived the verdict from first principles before trusting it — and that scrutiny is exactly what surfaced borderline cases like TC07.
