# NLP-project

# ATC Readback Verifier

A Streamlit web app that checks whether a pilot's spoken-back clearance (the *readback*) faithfully matches the controller's *instruction*, and flags exactly what went wrong.

> University NLP group project (Option 1 — Application Development). This is a proof of concept, not production or operational software.

## Why

In air traffic control, a controller issues an instruction and the pilot reads it back so the controller can confirm it was heard correctly. Wrong or incomplete readbacks — a substituted altitude, transposed digits, an omitted item — are a documented contributor to aviation incidents (e.g. NASA's Aviation Safety Reporting System). This tool acts as an automatic second check on that loop.

**Scope:** text input only. Live audio / speech-to-text is a possible future direction and is **not** built here.

## What it does

You enter the controller **instruction** and the pilot **readback** as text. The system extracts structured fields from each, compares them field by field, and returns a verdict: **MATCH**, or **DISCREPANCY** with a list of specific problems.

**Correct readback → MATCH**

```text
Instruction: Speedbird 245, descend flight level 240.
Readback:    Descend flight level 240, Speedbird 245.
Verdict:     MATCH — readback is correct.
```

**Wrong altitude → DISCREPANCY**

```text
Instruction: Speedbird 245, descend flight level 240.
Readback:    Descend flight level 250, Speedbird 245.
Verdict:     DISCREPANCY — 1 issue(s) found:
             • instructed altitude FL240, read back as FL250   [value_substitution]
```

The verifier extracts and compares **eight fields** — `callsign`, `altitude`, `heading`, `speed`, `frequency`, `squawk`, `runway`, `qnh` — and classifies each problem into one of five error categories:

| Category | Meaning | Example |
| --- | --- | --- |
| `value_substitution` | a different value was read back | FL240 → FL250 |
| `digit_transposition` | same digits, different order (higher-risk) | runway 21 → 12; squawk 5701 → 5071 |
| `omission` | an instructed item was not read back | — |
| `callsign_error` | callsign wrong or missing | Speedbird 245 → 254 |
| `added_element` | readback contains an item not instructed | — |

A correct readback yields zero discrepancies, which is a MATCH.

## Architecture

A **hybrid** pipeline. The LLM does only field extraction; every judgement (what matches, error category, normalization) is **deterministic Python we wrote**.

```text
  instruction text + readback text
            │
            ▼
   ┌──────────────────┐   LLM turns each message into structured fields
   │    Extractor     │   (swappable: ollama | hf)
   └──────────────────┘
            │  ExtractedFields × 2
            ▼
   ┌──────────────────┐   deterministic, field-by-field — the core IP
   │    Comparator    │   (no LLM, no tokens; unit-tested)
   └──────────────────┘
            │  list[Discrepancy]
            ▼
   ┌──────────────────┐
   │     Verdict      │   MATCH, or DISCREPANCY + specific problems
   └──────────────────┘
```

Public API:

```python
from atc_verifier import verify

result = verify(instruction, readback)
result.status            # "MATCH" or "DISCREPANCY"
result.verdict.summary() # human-readable explanation
```

## Quickstart

Requires Python ≥ 3.10. Run all commands from the repo root.

```bash
make setup             # create .venv, install runtime + dev deps, install package (-e)
cp .env.example .env   # then edit values (backend, model, token)
make pull-model        # ollama pull qwen2.5:3b  (local backend only)
make run               # launch the Streamlit app
```

The local (`ollama`) backend needs the [Ollama](https://ollama.com) server running and the model pulled via `make pull-model`. To run the evaluation harness or the unit tests instead:

```bash
make eval   # run the verifier over the labelled test set -> eval/results/
make test   # unit-test the comparator (no LLM, no token needed)
make lint   # ruff check
make fmt    # ruff format + ruff check --fix
```

<details>
<summary>Manual equivalents (without the Makefile)</summary>

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt && pip install -e .
cp .env.example .env          # then edit values
ollama pull qwen2.5:3b
streamlit run app/streamlit_app.py
python eval/run_eval.py
pytest
```

</details>

## Backends

Both extractor backends are free. Select one with the `EXTRACTOR_BACKEND` env var (in `.env`).

| Backend | `EXTRACTOR_BACKEND` | Runs | Default model | Used for |
| --- | --- | --- | --- | --- |
| Ollama | `ollama` | Locally, offline | `qwen2.5:3b` (`qwen2.5:7b` optional) | Development + the reproducible eval run |
| Hugging Face | `hf` | Inference API (free `HF_TOKEN`, Read scope) | `Qwen/Qwen2.5-7B-Instruct` | The hosted Streamlit Cloud demo |

Relevant env vars (set in `.env`, copied from `.env.example`): `EXTRACTOR_BACKEND`, `MODEL_NAME` (override), `HF_TOKEN` (only for `hf`), `OLLAMA_HOST` (optional). The hosted demo uses `hf` because the cloud free tier cannot run a local model.

## Evaluation & results

The test set `eval/data/atc_readback_test_set.csv` holds **50 labelled cases** (`TC01`..`TC50`) covering MATCH plus every error category. `make eval` runs the verifier over it and writes to `eval/results/`:

- `metrics.md` / `metrics.json` — headline metrics
- `predictions.csv` — per-case audit trail (predicted vs expected, extracted fields)
- `failures.md` — misclassified cases for the failure-mode analysis

Metrics reported: precision / recall / F1 for error detection (positive class = readback contains an error), false-alarm rate on correct readbacks, verdict accuracy, per-error-category detection recall, and a confusion matrix.

See **[`eval/results/metrics.md`](eval/results/metrics.md)** for the numbers, and run `make eval` to regenerate them.

**Latest result** — local `ollama` / `qwen2.5:3b`, 50 cases:

| Precision | Recall | F1 | False-alarm rate | Verdict accuracy |
| --- | --- | --- | --- | --- |
| 97.1% | 100.0% | 98.6% | 6.2% | 98.0% |

Detection recall is **100% in every error category**. These numbers reflect an iteration
documented in the failure analysis: a naïve prompt-hardening attempt *regressed* (false-alarm
12.5% → 25%) by poisoning the small model's extraction with over-specific few-shot examples; a
principled fix — a deterministic comparator rule for runway side plus safe prompt *rules* — then
improved on the baseline (F1 95.7% → 98.6%, false-alarm 12.5% → 6.2%). The one remaining failure
is an extraction miss, not a comparator error. Regenerate with `make eval`; full breakdown in
[`eval/results/metrics.md`](eval/results/metrics.md), and see the
[analysis notebook](notebooks/analysis.ipynb) and [failure analysis](docs/report/failure_analysis.md).

## Repository layout

```text
app/streamlit_app.py                       the web UI
src/atc_verifier/
  schema.py                                typed 8-field schema + normalization
  compare.py                               deterministic comparator (core IP)
  verdict.py                               verdict + result types
  extract/
    base.py                                Extractor interface + factory
    ollama_backend.py                      local backend
    hf_backend.py                          Hugging Face backend
    prompts/extract_fields.txt             few-shot extraction prompt
eval/
  run_eval.py, metrics.py                  evaluation harness
  data/atc_readback_test_set.csv           50 labelled cases
  results/                                 metrics.md, predictions.csv, failures.md
tests/                                     comparator, extraction & metrics unit tests (no LLM)
notebooks/
  build_notebook.py                        regenerates the analysis notebook
  analysis.ipynb                           reproducible end-to-end analysis + figures
docs/report/
  technical_report.md  executive_summary.md  field_review.md  failure_analysis.md
  use_of_ai_tools.md   slides.md                            report sources
  pdf/                                                      built submission PDFs
docs/reflections/                          six individual reflections
.github/workflows/ci.yml                   ruff + pytest on Python 3.11 & 3.12
Makefile  requirements.txt  requirements-dev.txt  pyproject.toml  .env.example
```

## Documentation

- [Install & execution guide](docs/INSTALL.md)
- [User manual](docs/USER_MANUAL.md)
- [Analysis notebook](notebooks/analysis.ipynb) — reproduces every number and figure

### Submission deliverables (PDF)

Committed under [`docs/report/pdf/`](docs/report/pdf/):

- **Technical report** — `ATC_Readback_Verifier_Technical_Report.pdf` (with field review, failure analysis, and use-of-AI appendices)
- **One-page executive summary** — `ATC_Readback_Verifier_Executive_Summary.pdf`
- **Slides** — `ATC_Readback_Verifier_Slides.pdf`
- **Individual reflections** — `ATC_Readback_Verifier_Individual_Reflections.pdf` (sources in [`docs/reflections/`](docs/reflections/))

## Team

| Member | Proposed role |
| --- | --- |
| Jan | App / UI & hosting (owns `app/`, Streamlit Cloud deploy) — repo owner |
| Vlad | Comparator core IP (owns `compare.py`, `verdict.py`, `schema.py`) |
| Felipe | Extraction & prompts (owns `src/atc_verifier/extract/`) |
| Alberto | Evaluation & metrics (owns `eval/`) |
| Kishan | Test set & data quality (owns `eval/data/`) |
| Yi | Report, field review & coordination (owns `docs/report/`) |

Roles are a starting point; the team can swap freely. Everyone writes their own `docs/reflections/<name>.md`.

## Live demo

Hosted on Streamlit Community Cloud: **https://ejjhv6jjt6hv8qfkfmqpxa.streamlit.app/**

**Academic integrity / Use of AI tools:** AI assistance used on this project is documented in the report's required "Use of AI tools" section.
