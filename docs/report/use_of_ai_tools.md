# Use of AI tools

The assignment explicitly encourages using LLMs, while requiring that the
**substantive intellectual decisions remain the team's own**. This section records
how we used AI assistance and where the team's own judgement governed.

## Where we used AI assistance

- **Brainstorming and scoping.** We used an LLM assistant to pressure-test the
  project shape (hybrid LLM-extraction + deterministic comparison), the choice of
  free/local tooling, and the repository structure.
- **Boilerplate and scaffolding.** Packaging (`requirements`, `pyproject`,
  `Makefile`), the Streamlit app shell and styling, the CI workflow, the evaluation
  harness plumbing, and documentation drafts were AI-assisted, then reviewed by us.
- **Prompt drafting and iteration.** The few-shot extraction prompt was drafted with
  AI help; we then iterated it against our own failure cases (see the failure
  analysis) and decided which fixes to keep based on measured results.
- **Drafting prose.** First drafts of this report's sections, the README, the install
  guide, and the user manual were AI-assisted. The team edited and verified them.
- **Literature search.** We used AI-assisted web search to locate candidate sources
  for the field review; **every citation was checked against the original source by a
  team member** before inclusion.

## What the team decided and owns

These were **not** delegated to the model; they are our own decisions and we can
defend each one:

- **Problem framing**: verifying read-back *correctness*, not transcription.
- **Test-set design and labels**: the 50 instruction/read-back pairs and their
  `expected_verdict` / `error_category` / `affected_field` labels, including the
  deliberate hard cases.
- **The error taxonomy**: the five categories (`value_substitution`,
  `digit_transposition`, `omission`, `callsign_error`, `added_element`) and their
  definitions.
- **Comparison logic**: what counts as a match, the normalization rules (units,
  spelled-out numbers, telephony, trailing zeros), and the policy on which items are
  *mandatory* to read back (e.g. wind is informational and not required).
- **Evaluation methodology**: the metric choices, including reporting false-alarm
  rate, and the framing of error detection as the positive class.
- **Error interpretation**: the hypotheses in the failure analysis and the
  conclusions drawn from the metrics.

## Tools used

| Tool | Used for |
|---|---|
| LLM coding/writing assistant | brainstorming, scaffolding, draft code & prose, debugging, literature search |

Two LLMs are **part of the product itself**, not authoring aids: the extractor
backends **`qwen2.5:3b`** (local, via Ollama) and **`Qwen/Qwen2.5-7B-Instruct`**
(Hugging Face Inference API). These perform **field extraction only** and are a
component of the system, documented in the system design.

## Verification & accountability

Code produced with assistance is covered by unit tests (`tests/test_compare.py`) and
a reproducible evaluation run; prose was fact-checked against the actual repository;
citations were verified against primary sources. Where AI output was wrong or
unsuitable, we corrected or discarded it.

> **Q&A reminder:** every member must be able to **explain and defend** the design,
> label definitions, methodology, and results, independent of any AI assistance used
> to produce them.
